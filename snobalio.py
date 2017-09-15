from ctypes import *
from datetime import datetime, timedelta
from copy import deepcopy

import numpy as np
from numpy.ctypeslib import ndpointer, as_array

nd_double_1d = ndpointer(np.float64, ndim=1, flags='C')
nd_double_2d = ndpointer(np.uintp, ndim=1, flags='C')


class ModelParams(Structure):
    """
    The model_params struct in c
    """
    _fields_ = [
        ("run_no_snow", c_int),
        ("stop_no_snow", c_int),
        ("max_z_s_0", c_double),
        ("max_h2o_vol", c_double),
        ("time_step", c_double),
        ("current_time", c_double),
        ("time_since_out", c_double)
    ]


class ModelStates(Structure):
    """
    The model_states struct in c
    """
    _fields_ = [
        ("z_s", c_double),
        ("rho", c_double),
        ("T_s", c_double),
        ("T_s_0", c_double),
        ("T_s_l", c_double),
        ("h2o_sat", c_double)
    ]


class ModelClimateInputs(Structure):
    """
    The model_climate_inputs struct in c
    """
    _fields_ = [
        ("S_n", c_double),
        ("I_lw", c_double),
        ("T_a", c_double),
        ("e_a", c_double),
        ("u", c_double),
        ("T_g", c_double)
    ]


class ModelMeasureParams(Structure):
    """
    The model_measure_params struct in c
    """
    _fields_ = [
        ("relative_hts", c_int),
        ("elevation", c_double),
        ("z_g", c_double),
        ("z_u", c_double),
        ("z_T", c_double),
        ("z_0", c_double)
    ]


class ModelMeasureParams1d(Structure):
    """
    The model_measure_params struct in c
    """
    _fields_ = [
        ("relative_hts", c_int),
        ("z_g", c_double),
        ("z_u", c_double),
        ("z_T", c_double),
        ("z_0", c_double),
        ("i_elevation", nd_double_1d)
    ]


class ModelPrecipInputs(Structure):
    """
    The model_precip_inputs struct in c
    """
    _fields_ = [
        ("precip_now", c_int),
        ("m_pp", c_double),
        ("percent_snow", c_double),
        ("rho_snow", c_double),
        ("T_pp", c_double)
    ]


class Snobal(object):

    def __init__(self, model_params, model_measure_params, elevations, initial_states, initial_timestamp):
        """
        intialize Snobal model

        Parameters
        ----------
        model_params : np.ndarray, (7, ), length needs to be 7, which are:
            0: run_no_snow: model continue running even when there is no snow, 1
            1: stop_no_snow: model stops when there is no snow, 0
            2: max_z_s_0: maximum active layer thickness, 0.5
            3: max_h2o_vol: maximum liquid h2o content as volume ratio, 0.1
            4: time_step: 3600 sec
            5: current_time: 0 sec
            6: time_since_out: 0 sec

        model_measure_params : np.ndarray, (5, ), length needs to be 5, which are:
            0: relative_hts: boolean, 1 if measurements heights, 0 if they are relative to surface
            1: z_g: depth of soil temp meas, 0.25
            2: z_u: height of wind measurement, 10
            3: z_T: height of air temp measurement, 10
            4: z_0: roughness length, 0.1

        elevations : np.ndarray, (n, ), an array of elevations of modeling pixels

        initial_states : np.ndarray, (6, n), a 2-D array, each column is a state vector, which are
            0: z_s: snowdepth, m
            1: rho: average snow density, kg/m^3
            2: T_s: average snow cover temperature, K (Kelvin)
            3: T_s_0: active snow layer temperature, K (Kelvin)
            4: T_s_l: lower layer temperature, K (Kelvin)
            5: h2o_sat: % of liquid H2O saturation
        """
        assert isinstance(model_params, np.ndarray)
        assert isinstance(model_measure_params, np.ndarray)
        assert isinstance(elevations, np.ndarray)
        assert isinstance(initial_states, np.ndarray)
        assert isinstance(initial_timestamp, datetime)
        self.model_params = model_params
        self.model_measure_params = model_measure_params
        self.elevations = elevations
        self.states_0 = initial_states
        self._c_states = self.states_0.copy()
        assert len(self.elevations) == self.states_0.shape[1]
        self._snobal = None
        self._init_snobal()
        self._swe = self.states_0[0] * self.states_0[1]    # Please note that the SWE are in mm
        self._c_swe = self.states_0[0] * self.states_0[1]
        self._timelist = [initial_timestamp]

    def _init_snobal(self):
        self._snobal = CDLL('/media/raid0/zeshi/isnobal/SnobalIO/cmake-build-debug/libSnobalIO.so')

        self._snobal.run_snobal.argtypes = (POINTER(ModelParams),
                                            POINTER(ModelMeasureParams),
                                            POINTER(ModelStates),
                                            POINTER(ModelClimateInputs),
                                            POINTER(ModelClimateInputs),
                                            POINTER(ModelPrecipInputs))
        self._snobal.run_snobal.restype = POINTER(ModelStates)

        self._snobal.run_isnobal_1d.argtypes = (
            c_long,
            POINTER(ModelParams),
            POINTER(ModelMeasureParams1d),
            nd_double_2d,
            nd_double_2d,
            nd_double_2d,
            nd_double_2d
        )

        self._snobal.run_isnobal_1d.restype = POINTER(POINTER(c_double))
        return 0

    def run_isnobal_1d(self, climate_inputs1, precip_inputs, climate_inputs2=None):
        """
        run_isnobal for one time-step

        Parameters
        ----------
        climate_inputs1 : np.ndarray, (6, n), climate inputs, which are:
            S_n: net solar radiation (W/m^2)
            I_lw: incoming longwave (thermal) rad (W/m^2)
            T_a: air temp (Kelvin)
            e_a: vapor pressure (Pa)
            u: wind speed (m/sec)
            T_g: soil temp at depth z_g (Kelvin)

        precip_inputs : np.ndarray, (5, n), precip inputs, which are:
            precip_now: precipitation occur for current timestep?
            m_pp: specific mass of total precip (kg/m^2), mm of water
            percent_snow: % of total mass that's snow (0 to 1.0)
            rho_snow: density of snowfall (kg/m^3)
            T_pp: precip temp (Kelvin)

        climate_inputs2 : np.ndarray, same as climate_input1 but the end of current timestep
        """
        i_states = deepcopy(self._c_states)
        pixel_length = i_states.shape[1]

        # Assertion control on input1
        i_inputs1 = climate_inputs1

        # Assertion control on precip
        i_precips = precip_inputs

        # Assertion control on DEM
        i_elevations = self.elevations

        # Assertion control on measure
        measure_params = self.model_measure_params

        params = self.model_params

        if climate_inputs2 is not None:
            i_inputs2 = climate_inputs2
        else:
            i_inputs2 = np.copy(i_inputs1)

        assert i_inputs1.shape[1] == pixel_length, "inputs and states shape has to match"
        assert i_precips.shape[1] == pixel_length, "precip inputs and states shape has to match"

        result = self._run_isnobal_1d(params=params,
                                      measure_params=measure_params,
                                      i_elevation=i_elevations,
                                      i_states=i_states,
                                      i_inputs1=i_inputs1,
                                      i_inputs2=i_inputs2,
                                      i_precips=i_precips)
        self._c_states = result
        self._swe = np.column_stack((self._swe, self._c_states[0] * self._c_states[1]))
        self._c_swe = self._swe[:, -1]
        self._timelist.append(self._timelist[-1] + timedelta(seconds=self.model_params[4]))
        return 0

    def get_swe(self):
        return self._c_swe

    def get_all_swes(self):
        return self._timelist, self._swe

    def _run_isnobal_1d(self, params, measure_params, i_elevation, i_states, i_inputs1, i_inputs2, i_precips):
        model_params_obj = self._construct_model_params(params)
        model_measure_params_1d = self._construct_model_measure_params_1d(measure_params, i_elevation)
        p_results = self._snobal.run_isnobal_1d(c_long(i_states.shape[1]),
                                                byref(model_params_obj),
                                                byref(model_measure_params_1d),
                                                self._convert_2d(i_states),
                                                self._convert_2d(i_inputs1),
                                                self._convert_2d(i_inputs2),
                                                self._convert_2d(i_precips))
        arr_results = self._read_isnobal_results(p_results, i_states.shape[1])
        return arr_results

    @staticmethod
    def _read_isnobal_results(p_results, n_pixels):
        arr_results = np.zeros((6, n_pixels))
        for i in range(6):
            arr_results[i] = as_array(p_results[i], shape=(n_pixels, ))
        return arr_results

    @staticmethod
    def _construct_model_params(params):
        """
        A constructor of model_params object
        :param params: Could be a list/1-D array of the values specified in model_params
        :return: an instance of object model_params
        """
        return ModelParams(int(params[0]),
                           int(params[1]),
                           float(params[2]),
                           float(params[3]),
                           float(params[4]),
                           float(params[5]),
                           float(params[6]))

    @staticmethod
    def _construct_model_states(states):
        """
        A constructor of model_states object
        :param states: Could be a list/1-D array of the values specified in model_states
        :return: an instance of object model_states
        """
        return ModelStates(float(states[0]),
                           float(states[1]),
                           float(states[2]),
                           float(states[3]),
                           float(states[4]),
                           float(states[5]))

    @staticmethod
    def _construct_model_climate_inputs(climate_inputs):
        """
        A constructor of model_climate_inputs object
        :param climate_inputs: Could be a list/1-D array of the values specified in
        model_climate_inputs.

        :return: an instance of object model_climate_inputs
        """
        return ModelClimateInputs(float(climate_inputs[0]),
                                  float(climate_inputs[1]),
                                  float(climate_inputs[2]),
                                  float(climate_inputs[3]),
                                  float(climate_inputs[4]),
                                  float(climate_inputs[5]))

    @staticmethod
    def _construct_model_measure_params(measure_params):
        """
        A constructor of model_measure_params object
        :param measure_params: Could be a list/1-D array of the values specified in
        model_measure_params.

        :return: an instance of object model_measure_params
        """
        return ModelMeasureParams(int(measure_params[0]),
                                  float(measure_params[1]),
                                  float(measure_params[2]),
                                  float(measure_params[3]),
                                  float(measure_params[4]),
                                  float(measure_params[5]))

    @staticmethod
    def _construct_model_precip_inputs(precip_inputs):
        """
        A constructor of model_precip_inputs object
        :param precip_inputs: Could be a list/1-D array of the values specified in
        model_precip_inputs

        :return: an instance of object model_precip_inputs
        """
        return ModelPrecipInputs(int(precip_inputs[0]),
                                 float(precip_inputs[1]),
                                 float(precip_inputs[2]),
                                 float(precip_inputs[3]),
                                 float(precip_inputs[4]))

    @staticmethod
    def _convert_2d(array):
        assert isinstance(array, np.ndarray)
        return (array.ctypes.data + np.arange(array.shape[0]) * array.strides[0]).astype(np.uintp)

    @staticmethod
    def _parse_states(state_result):
        try:
            result = np.array([state_result.contents.z_s,
                               state_result.contents.rho,
                               state_result.contents.T_s,
                               state_result.contents.T_s_0,
                               state_result.contents.T_s_l,
                               state_result.contents.h2o_sat])
            return result
        except ValueError:
            print "The model returned NULL pointer, check input values."
            return None

    @staticmethod
    def _construct_model_measure_params_1d(measure_params, i_elevation):
        """

        :param measure_params: relative_hts, z_g, z_u, z_T, z_0
        :param i_elevation:
        :return:
        """
        return ModelMeasureParams1d(int(measure_params[0]),
                                    float(measure_params[1]),
                                    float(measure_params[2]),
                                    float(measure_params[3]),
                                    float(measure_params[4]),
                                    i_elevation.ctypes.data)

    def run_snobal(self, **kwargs):
        """
        Running the snobal model through this wrapper
        :param kwargs:
        states: list/1-D array, length = 6
        climate_inputs1: list/1-D array
        params = None


        :return:
        """
        # Assertion of correctness of states kwarg
        assert "states" in kwargs, "User must specify the initial states of the snowpack!"
        assert len(kwargs.get("states")) == 6, "Please check the length of states!"

        # Assertion of correctness of climate_inputs1 kwarg
        assert "climate_inputs1" in kwargs, ("User must specify the climate condition " +
                                             "at the start of the time step!")
        assert len(kwargs.get("climate_inputs1")) == 6, "Please check the length of climate_inputs1"

        # Assertion of correctness of precip_inputs kwarg
        assert "precip_inputs" in kwargs, "User must specify the precipitation condition!"
        assert len(kwargs.get("precip_inputs")) == 5, "Please check the length of precip_inputs"

        if "params" in kwargs:
            assert len(kwargs.get("params")) == 7, "Please check the length of model_params"
            params = byref(Snobal._construct_model_params(kwargs.get("params")))
        else:
            params = None

        if "measure_params" in kwargs:
            assert len(kwargs.get("measure_params")) == 6, "Please check the length of measure_params"
            measure_params = byref(Snobal._construct_model_measure_params(kwargs.get("measure_params")))
        else:
            measure_params = None

        states = byref(Snobal._construct_model_states(kwargs.get("states")))
        climate_inputs1 = byref(Snobal._construct_model_climate_inputs(kwargs.get("climate_inputs1")))
        precip_inputs = byref(Snobal._construct_model_precip_inputs(kwargs.get("precip_inputs")))

        if "climate_inputs2" in kwargs:
            assert len(kwargs.get("climate_inputs2")) == 6, "Please check the length of climate_inputs2"
            climate_inputs2 = byref(Snobal._construct_model_climate_inputs(kwargs.get("climate_inputs2")))
        else:
            climate_inputs2 = None

        result = self._snobal.run_snobal(params,
                                         measure_params,
                                         states,
                                         climate_inputs1,
                                         climate_inputs2,
                                         precip_inputs)

        res_states = Snobal._parse_states(result)
        return res_states

    @staticmethod
    def _compile_states_dict(states_dict):

        fields = ["z_s", "rho", "T_s", "T_s_0", "T_s_l", "h2o_sat"]

        assert all(k in states_dict for k in fields), \
            "User has missed one field in states!"

        # Assume the snowdepth pixel length is the standard by default
        pixel_length = states_dict["z_s"].shape[0]
        i_states = np.zeros((6, pixel_length))
        for i, k in enumerate(fields):
            assert len(states_dict[k].shape) == 1, \
                "Processing error, each attribute of states has to be 1D array"
            assert states_dict[k].shape[0] == pixel_length, \
                "Processing error, states length are not the same!"
            i_states[i] = states_dict[k]
        return pixel_length, i_states

    @staticmethod
    def _compile_input_dict(input_dict, pixel_length, input_type='climate'):
        if input_type == 'climate':
            fields = ["S_n", "I_lw", "T_a", "e_a", "u", "T_g"]
        else:
            fields = ["precip_now", "m_pp", "percent_snow", "rho_snow", "T_pp"]

        assert all(k in input_dict for k in fields), \
            "User has missed some attribute(s) in input!"

        i_input = np.zeros((len(fields), pixel_length))
        for i, k in enumerate(fields):
            assert len(input_dict[k].shape) == 1, \
                "Processing error, each attribute of input has to be 1D array"
            assert input_dict[k].shape[0] == pixel_length, \
                "Processing error, input length are not the same!"
            i_input[i] = input_dict[k]
        return i_input
