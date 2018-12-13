import numpy as np
import json

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

    def ith(self,i):
        return GaussDist(self._mu[i],self._sigma[i])

    def to_json(self):
        return {
            'dist':'normal',
            'mu':self._mu,
            'sigma':self._sigma
        }

    def __repr__(self):
        return "N(%s,%s)" % (self._mu,self._sigma)

class MultiGaussDist:

    def __init__(self,mus,sigmas):
        self._mus = np.array(mus)
        self._sigmas = np.array(sigmas)
        self._n = len(mus)


    def from_samples(values):
        if len(values) == 0:
            return GaussDist(0.0,0.0)

        mus = list(map(lambda vs: np.mean(vs), values))
        sigmas = list(map(lambda vs: np.std(vs), values))
        return MultiGaussDist(mus,sigmas)


    def to_json(self):
        return {
          'dist': 'multi-normal',
          'mu': list(self._mus),
          'sigma': list(self._sigmas),
          'n':self._n
        }

class StochTimeXform:
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

class StochSignalXform:
    class StochSegment:

        # m*x + b + N(mu,sig)
        def __init__(self,lb,ub,slope,offset,biases):
            self._lower_bound = lb
            self._upper_bound = ub
            self._slope = slope
            self._offset = offset
            if isinstance(biases, GaussDist):
                self._bias = biases
            else:
                self._bias = GaussDist.from_samples(biases)

        @staticmethod
        def from_deterministic_model(seg,biases):
            return StochSignalXform.StochSegment(
                seg.lower_bound,
                seg.upper_bound,
                seg.alpha,
                seg.beta,
                biases
            )

        @staticmethod
        def from_json(data):
            seg = SignalXformModel.StochSegment(
                lb=data['lower_bound'],
                ub=data['upper_bound'],
                slope=data['slope'],
                offset=data['offset'],
                biases=GaussDist.from_json(data['bias'])
            )
            return seg


        def to_json(self):
            return {
                'slope':self._slope,
                'offset':self._offset,
                'bias':self._bias.to_json(),
                'lower_bound':self._lower_bound,
                'upper_bound':self._upper_bound
            }


        def __repr__(self):
            return "[%s,%s]\t\t%s*x+%s+%s" % \
                (self._lower_bound,self._upper_bound,\
                 self._slope,
                 self._offset,\
                 self._bias)

    def __init__(self):
        self._segments = []

    def add_segment(self,seg):
        assert(isinstance(seg,StochSignalXform.StochSegment))
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

class StochLinNoiseXformModel:

    def __init__(self,freqs,slopes,offsets,samples):
         self._freqs = freqs
         self._slopes = slopes
         self._offsets = offsets
         if isinstance(samples,MultiGaussDist):
             self._rvs = samples
         else:
             self._rvs = MultiGaussDist.from_samples(samples)

    def stumps(self):
        for i,(freq,slope,offset,mu,std) in \
            enumerate(zip(self._freqs,
                self._slopes,
                self._offsets)):
            yield freq,slope,offset,self._rvs.ith(i)

    @staticmethod
    def from_deterministic_model(det_mod,errors):
        return StochLinNoiseXformModel(
            det_mod.freqs,
            det_mod.slopes(0),
            det_mod.offsets,
            errors
        )


    def to_json(self):
        return {
            'freqs':list(self._freqs),
            'slopes':list(self._slopes),
            'offsets':list(self._offsets),
            'rvs':self._rvs.to_json()
        }
