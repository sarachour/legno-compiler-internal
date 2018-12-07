import json

class BlackBoxModel:

    def __init__(self):
        self._phase = None
        self._freqs = None
        self._parameters = {}

    def phase_model(self):
        return self._phase['mean'],self._phase['stdev']

    def add_noise_model(self,freqs):
        self._freqs = freqs

    def add_parameter(self,param,mean,stdev):
             self._parameters[param] = {'mean':list(mean),
                                       'stdev':list(stdev)}

    def add_phase_model(self,mean,std):
        self._phase = {
            'mean':mean,'stdev':std
        }

    def to_json(self):
        return {
            'phase_model':{'mean':self._phase['mean'],
                           'stdev':self._phase['stdev']},
            'noise_model':{
                'freqs':self._freqs,
                'params': self._parameters
            }
        }

    @staticmethod
    def from_json(obj):
        bmod = BlackBoxModel()
        bmod.add_noise_model(obj['noise_model']['freqs'])
        bmod.add_phase_model( \
                              obj['phase_model']['mean'],
                              obj['phase_model']['stdev']
        )

        for param,data in obj['noise_model']['params'].items():
            bmod.add_parameter(param,data['mean'],data['stdev'])

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
