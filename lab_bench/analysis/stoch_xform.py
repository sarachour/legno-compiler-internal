import numpy as np
import json
import scipy
import lab_bench.analysis.det_xform as dx
import scipy.stats
import itertools

class GaussDist:
    def __init__(self,mu,sigma):
        self._mu = mu
        self._sigma = sigma
        self._dist = scipy.stats.norm(mu,sigma)

    def from_samples(values):
        if len(values) == 0:
            return GaussDist(0.0,0.0)

        mu = np.mean(values)
        sigma = np.std(values)
        return GaussDist(mu,sigma)

    def ith(self,i):
        return GaussDist(self._mu[i],self._sigma[i])

    def pdf(self,value):
        prob = self._dist.pdf(value)
        return 1.0 if prob > 1.0 else prob

    def stds(self,value):
      return float(value-self._mu)/self._sigma

    def to_json(self):
        return {
            'dist':'normal',
            'mu':self._mu,
            'sigma':self._sigma
        }

    @staticmethod
    def from_json(data):
        assert(data['dist'] == 'normal')
        return GaussDist(data['mu'],data['sigma'])


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

    @property
    def mu(self):
      return self._mus

    @property
    def sigma(self):
      return self._sigmas

    def to_json(self):
        return {
          'dist': 'multi-normal',
          'mu': list(self._mus),
          'sigma': list(self._sigmas),
        }

    @staticmethod
    def from_json(data):
        assert(data['dist'] == 'multi-normal')
        return MultiGaussDist(data['mu'],data['sigma'])

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

    @property
    def delay(self):
        return self._delay

    @staticmethod
    def from_json(data):
        return StochTimeXform(
          GaussDist.from_json(data['delay']),
          GaussDist.from_json(data['warp'])
        )

    def to_json(self):
        return {
            'delay': self._delay.to_json(),
            'warp': self._warp.to_json()
        }

    def __repr__(self):
        return "delay=%s, warp=%s" % (self._delay,self._warp)


class DetSignalXformVariance(dx.DetSignalXform):

    def __init__(self,freqs,slopes,offsets,nsamps):
        dx.DetSignalXform.__init__(self,freqs,slopes,offsets,nsamps)

    @staticmethod
    def from_json(data):
        return DetLinearModel.from_json(DetSignalXformVariance,data)

    @staticmethod
    def read(filename):
        DetLinearModel.read(DetSignalXformVariance,filename)

    def apply_one(self,i,v):
        pred = self.offset[i]
        return pred

    def apply(self,v):
        return self.offset



class DetNoiseModelVariance(dx.DetNoiseModel):

    def __init__(self,freqs,slopes,offsets,nsamps):
        dx.DetNoiseModel.__init__(self,freqs,slopes,offsets,nsamps)

    @staticmethod
    def from_json(data):
        return DetLinearModel.from_json(DetNoiseModelVariance,data)

    @staticmethod
    def read(filename):
        DetLinearModel.read(DetNoiseModelVariance,filename)

    def apply_one(self,i,v):
        return self.slope(0)[i]*v + self.offset[i]

    def apply(self,v):
        return self.slope(0)*v + self.offset





class StochLinearModel:


    def __init__(self,mean,std):
      self._mean = mean
      self._stdev = std

    @property
    def mean(self):
      return self._mean

    @property
    def stdev(self):
      return self._stdev

    def apply2(self,locs,values):
      mean = self._mean.apply2(locs,values)
      variance = self._stdev.apply2(locs,values)
      return MultiGaussDist(mean,variance)

    def dist(self,loc,val):
      mu = self._mean.apply2_el(loc,val)
      std = self._stdev.apply2_el(loc,val)
      return GaussDist(mu,std)

    def to_json(self):
        return {
            'type': 'stoch-linear-model',
            'mu':self._mean.to_json(),
            'sigma':self._stdev.to_json()
        }

    @staticmethod
    def from_json(data):
      raise Exception("implement me")
