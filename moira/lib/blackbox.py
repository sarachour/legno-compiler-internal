import json
import numpy as np
import lab_bench.analysis.stoch_xform as sx

# TODO: characterize black-box model

class BlackBoxModel:

    def __init__(self,time_model,disto_model,noise_model):
        self._time_model = time_model
        self._disto_model = disto_model
        self._noise_model = noise_model


    def to_json(self):
        return {
            'time': self._time_model.to_json(),
            'disto': self._disto_model.to_json(),
            'noise': self._noise_model.to_json()
        }

    @property
    def time_model(self):
        return self._time_model

    @property
    def disto_model(self):
        return self._disto_model

    @property
    def noise_model(self):
        return self._noise_model

    @staticmethod
    def from_json(obj):
        bmod = BlackBoxModel(
            sx.StochTimeXform.from_json(obj['time']),
            sx.StochSignalXform.from_json(obj['disto']),
            sx.StochLinNoiseXformModel.from_json(obj['noise'])
        )
        return bmod

    @staticmethod
    def read(filename):
        with open(filename,'r') as fh:
            obj = json.loads(fh.read())
            return BlackBoxModel.from_json(obj)

    def write(self,filename):
        jsonobj = self.to_json()
        jsonstr = json.dumps(jsonobj)
        with open(filename,'w') as fh:
            fh.write(jsonstr)
