import json
import numpy as np

# TODO: characterize black-box model

class GaussDist:
    def __init__(self,mu,sigma):
        self._mu = mu
        self._sigma = sigma

    def from_samples(values):
        if len(values) == 0:
            return GaussDist(0.0,0.0)

        mu = np.mean(values)
        sigma = np.std(values)
        return GaussDist(mu,sigma)

    def to_json(self):
        return {
            'dist':'normal',
            'mu':self._mu,
            'sigma':self._sigma
        }

    def __repr__(self):
        return "N(%s,%s)" % (self._mu,self._sigma)

class TimeXformModel:
    def __init__(self,delays,warps):
        if isinstance(delays, GaussDist):
            self._delay = delays
        else:
            self._delay = GaussDist.from_samples(abs(np.array(delays)))

        if isinstance(warps, GaussDist):
            self._warp = warps
        else:
            self._warp = GaussDist.from_samples(abs(np.array(warps)))

    def to_json(self):
        return {
            'delay': self._delay.to_json(),
            'warp': self._warp.to_json()
        }

    def __repr__(self):
        return "delay=%s, warp=%s" % (self._delay,self._warp)

class SignalXformModel:
    class Segment:

        # m*x + b + N(mu,sig)
        def __init__(self,lb,ub,slope,intercept,biases):
            self._lower_bound = lb
            self._upper_bound = ub
            self._slope = slope
            self._intercept = intercept
            if isinstance(biases, GaussDist):
                self._bias = biases
            else:
                self._bias = GaussDist.from_samples(biases)

        @staticmethod
        def from_xform_segment(seg,biases):
            return SignalXformModel.Segment(
                seg.lower_bound,
                seg.upper_bound,
                seg.alpha,
                seg.beta,
                biases
            )

        @staticmethod
        def from_json(data):
            seg = SignalXformModel.Segment(
                lb=data['lower_bound'],
                ub=data['upper_bound'],
                slope=data['slope'],
                intercept=data['intecept'],
                biases=GaussDist.from_json(data['bias'])
            )
            return seg


        def to_json(self):
            return {
                'slope':self._slope,
                'intercept':self._intercept,
                'bias':self._bias.to_json(),
                'lower_bound':self._lower_bound,
                'upper_bound':self._upper_bound
            }


        def __repr__(self):
            return "[%s,%s]\t\t%s*x+%s+%s" % \
                (self._lower_bound,self._upper_bound,\
                 self._slope,
                 self._intercept,\
                 self._bias)

    def __init__(self):
        self._segments = []

    def add_segment(self,seg):
        assert(isinstance(seg,SignalXformModel.Segment))
        self._segments.append(seg)


    def to_json(self):
        segj = list(map(lambda seg: seg.to_json(), \
                        self._segments))
        return {
            'type':'pwl',
            'segments':segj,
        }

    @staticmethod
    def from_json(data):
        xform = SignalXformModel()
        for seg_json in data['segments']:
            seg = SignalXformModel.Segment\
                                    .from_json(seg_json)
            xform._segments.append(seg)

        return xform


    def __repr__(self):
        r = ""
        for seg in self._segments:
            r += "%s\n" % seg

        return r

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
