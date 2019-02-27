import pyGPGO as pyg
from pyGPGO.surrogates.GaussianProcess import GaussianProcess
from pyGPGO.GPGO import GPGO



def BayesianOptimization:

    def __init__(self,fv):
        self._fv = fv


    def model():
        cov = pyg.covfunc.squaredExponential()
        pyg.acquisition.Acquisition(mode='ExpectedImprovement')
        gp = GaussianProcess(cov, optimize=True, usegrads=True)
        gpgo = GPGO(gp,acq,param)
