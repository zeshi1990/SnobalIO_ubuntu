from datetime import datetime

import numpy as np

from snobalio import Snobal

model_params = np.array([1, 0, 0.5, 0.1, 3600, 0, 0])
model_measure_params = np.array([1, 0.25, 10, 10, 0.1])
elevations = np.array([2500., 3000.])

states = np.array([[1.0, 0.8],
                   [300., 300.],
                   [273., 273.],
                   [273., 273.],
                   [0., 0.],
                   [0.2, 0.2]])

climate_inputs = np.array([[200., 300.],
                           [200., 300.],
                           [0., 0.],
                           [101325., 101325.],
                           [1.5, 1.5],
                           [0., 0.]])

precip_inputs = np.array([[0, 0],
                          [0, 0],
                          [0, 0],
                          [0, 0],
                          [0, 0]])

snobal = Snobal(model_params, model_measure_params, elevations, states, datetime(2014, 1, 1))
snobal.run_isnobal_1d(climate_inputs1=climate_inputs,
                      precip_inputs=precip_inputs,
                      climate_inputs2=climate_inputs)

print snobal.get_swe()

res = snobal.run_snobal(states=states[:, 0],
                        climate_inputs1=climate_inputs[:, 0],
                        precip_inputs=precip_inputs[:, 0],
                        params=model_params,
                        measure_params=np.append(model_measure_params, elevations[0]))
print res






