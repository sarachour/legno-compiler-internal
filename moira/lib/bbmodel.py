import json

# TODO: characterize black-box model

class LinearNoiseModel:

    def __init__(self,freqs,slopes,intercepts,errors):
        self._freqs = freqs
        self._slopes = slopes
        self._nsigs = len(slopes)
        self._offsets = intercepts
        self._errors = errors

    def to_json(self):
        slopes = {}
        for i in range(0,self._nsigs):
            slopes[i] = list(self._slopes[i])

        return {
            'type': 'linear',
            'freqs':list(self._freqs),
            'slopes': slopes,
            'offsets': list(self._offsets),
            'errors': list(self._errors)
        }

    def write(self,filename):
        with open(filename,'w') as fh:
            fh.write(json.dumps(self.to_json()))


class BlackBoxModel:
    class XformModel:
        def __init__(self,xform,uncertainty):
            self._xform = xform
            self._uncertainty = uncertainty

    def __init__(self):
        self._phase = None
        self._freqs = None
        self._parameters = {}


    def to_json(self):
        return {}

    @staticmethod
    def from_json(obj):
        bmod = BlackBoxModel()
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
