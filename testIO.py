from datetime import datetime

import numpy as np

from snobalio import Snobal

model_params = np.array([1, 0, 0.5, 0.1, 21600, 0, 0])
model_measure_params = np.array([1, 0.25, 10, 10, 0.1])
elevations = np.array([2500., 2500.])

states = np.array([[1.0, 0.8],
                   [300., 300.],
                   [273.16, 273.16],
                   [273.16, 273.16],
                   [273.16, 273.16],
                   [0.2, 0.2]])

climate_inputs = np.array([[200., 300.],
                           [200., 300.],
                           [275., 275.],
                           [101325., 101325.],
                           [1.5, 1.5],
                           [273.16, 273.16]])

precip_inputs = np.array([[0, 0],
                          [0, 0],
                          [0, 0],
                          [0, 0],
                          [273.16, 273.16]])

snobal = Snobal(model_params, model_measure_params, elevations, states, datetime(2014, 1, 1))
snobal.run_isnobal_1d(climate_inputs1=climate_inputs,
                      precip_inputs=precip_inputs,
                      climate_inputs2=climate_inputs)

print snobal.get_swe()

single_measure_params = np.array([1, 2500., 0.25, 10, 10, 0.1])

res = snobal.run_snobal(states=states[:, 0],
                        climate_inputs1=climate_inputs[:, 0],
                        cliamte_inputs2=climate_inputs[:, 0],
                        precip_inputs=precip_inputs[:, 0],
                        params=model_params,
                        measure_params=single_measure_params)

res1 = snobal.run_snobal(states=states[:, 1],
                         climate_inputs1=climate_inputs[:, 1],
                         cliamte_inputs2=climate_inputs[:, 1],
                         precip_inputs=precip_inputs[:, 1],
                         params=model_params,
                         measure_params=single_measure_params)

print res[0]*res[1]

assert snobal.get_swe()[0] == res[0] * res[1], "Failed"
assert snobal.get_swe()[1] == res1[0] * res1[1], "Failed"






