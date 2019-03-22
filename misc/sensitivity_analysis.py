from SALib.sample import saltelli
from SALib.analyze import sobol
import math
import numpy as np

def ET(X):
    # column 0 = C, column 1 = R, column 2 = t
  return np.sin(X[:,0])
  #return X[:,0]

problem = {'num_vars': 1,
           'names': ['x'],
           'bounds': [[-10, 10]]
           }

print("<< sample >")
nsamples = 100000
# Generate samples
#nsamples = 10000000
param_values = saltelli.sample(problem, nsamples, calc_second_order=False)

print("<< run model >")
# Run model (example)
Y = ET(param_values)

print("<< analyze>")
# Perform analysis
Si = sobol.analyze(problem, Y, print_to_console=True)
print(Si['S1'])
print(Si['ST'])
