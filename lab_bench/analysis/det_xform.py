import numpy as np
import json
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
#The following constant was computed in maxima 5.35.1 using 64 bigfloat digits of precision
import math


def sigfig( x, sigfigs ):
  __logBase10of2 = 3.010299956639811952137388947244e-1
  """
  Rounds the value(s) in x to the number of significant figures in sigfigs.

  Restrictions:
  sigfigs must be an integer type and store a positive value.
  x must be a real value or an array like object containing only \
  real values.
  """
  if not ( type(sigfigs) is int or np.issubdtype(sigfigs, np.integer)):
      raise TypeError( "RoundToSigFigs: sigfigs must be an integer." )

  if not np.all(np.isreal( x )):
      raise TypeError( "RoundToSigFigs: all x must be real." )

  if sigfigs <= 0:
      raise ValueError( "RoundtoSigFigs: sigfigs must be positive." )

  xsgn = np.sign(x)
  absx = xsgn * x
  mantissas, binaryExponents = np.frexp( absx )

  decimalExponents = __logBase10of2 * binaryExponents
  intParts = np.floor(decimalExponents)

  mantissas *= 10.0**(decimalExponents - intParts)

  if type(mantissas) is float or np.issctype(np.dtype(mantissas)):
      if mantissas < 1.0:
          mantissas *= 10.0

  elif np.issubdtype(mantissas, np.ndarray):
      fixmsk = mantissas < 1.0
      mantissas[fixmsk] *= 10.0

  return xsgn * np.around( mantissas, decimals=sigfigs - 1 ) \
    * 10.0**intParts



class DetTimeXform:
        def __init__(self,offset,warp=1.0):
            self._delay = offset
            self._warp = warp

        def set_warp(self,warp):
            self._warp = warp

        @property
        def warp(self):
            return self._warp


        @property
        def delay(self):
            return self._delay

        def to_json(self):
            return {
                    'delay':self._delay,
                    'warp': self._warp
            }
        @staticmethod
        def from_json(data):
            return DetTimeXform(data['delay'],data['warp'])

        def write(self,name):
            with open(name,'w') as fh:
                strdata = json.dumps(self.to_json())
                fh.write(strdata)

        @staticmethod
        def read(name):
            with open(name,'r') as fh:
                data = json.loads(fh.read())
                return DetTimeXform.from_json(data)


class DetLinearModel:

    def __init__(self,locs,slopes,offsets,num_samples):
        self._locs= np.array(locs)
        self._slopes = np.array(slopes)
        self._nsigs = len(slopes)
        self._nsamps = num_samples
        self._offsets = np.array(offsets)

    def slope(self,i):
        return self._slopes[i]

    @property
    def offset(self):
        return self._offsets

    def find_nearest_index(self,value):
        array = self._locs
        idx = np.searchsorted(array, value, side="left")
        if idx > 0 and (idx == len(array) or \
                        math.fabs(value - array[idx-1]) \
                        < math.fabs(value - array[idx])):
          return idx-1
        else:
          return idx

    @property
    def num_samples(self):
        return self._nsamps


    @property
    def locs(self):
        return self._locs

    def apply_one(self,i,value):
        raise NotImplementedError

    def apply(self,values):
        raise NotImplementedError

    def apply2(self,dlocs,values):
        inds = map(lambda v: self.find_nearest_index(v),dlocs)
        return np.array(list(
          map(lambda args: self.apply_one(*args), zip(inds,values))
        ))

    def to_json(self):
        slopes = {}
        for i in range(0,self._nsigs):
            slopes[i] = list(self._slopes[i])

        data = {
            'type': 'linear',
            'locs':list(self._locs),
            'slopes': slopes,
            'num_samples': list( \
                                 map(lambda i:int(i),
                                     self._nsamps)),
            'offsets': list(self._offsets)
        }
        return data

    @staticmethod
    def fit(dlocs,dep_vars,observations,nsigs):
        locs = sorted(set(dlocs))
        nlocs = len(locs)
        b_dep_variables = list(map(lambda _ : [], range(0,nlocs)))
        b_obs_variables = list(map(lambda _ : [], range(0,nlocs)))
        for dloc,dep_var,obs in \
            zip(dlocs,dep_vars,observations):
            dist = (locs-dloc)**2
            idx = np.argmin(dist)
            b_dep_variables[idx].append(dep_var)
            b_obs_variables[idx].append(obs)

        M = np.zeros((nsigs,nlocs),dtype=float)
        B = np.zeros(nlocs,dtype=float)
        N = np.zeros(nlocs,dtype=int)

        for idx in range(0,nlocs):
          v = locs[idx]
          xs = b_dep_variables[idx]
          ys = b_obs_variables[idx]
          if len(xs) == 0:
            continue

          N[idx] = len(ys)
          if nsigs == 0:
            coeff = np.mean(ys)
            B[idx] = coeff

          else:
            regr = linear_model.LinearRegression()
            regr.fit(xs,ys)
            ys_pred = regr.predict(xs)
            error = mean_squared_error(ys, ys_pred)
            print("%s] %s*x+%s, %s {%s}" % (v,regr.coef_,\
                                            regr.intercept_,\
                                            error,len(ys)))
            for k in range(0,nsigs):
              M[k][idx] = regr.coef_[k]

            B[idx] = regr.intercept_

        return locs,M,B,N

    def plot_num_samples(self,filename):
        plt.plot(self.locs,self.num_samples,linewidth=1)
        plt.savefig(filename)
        plt.cla()

    def plot_slope(self,filename,i):
        if self._nsigs == 0:
          plt.savefig(filename)
          plt.cla()
          return

        plt.plot(self.locs,self.slope(i),linewidth=1)
        plt.savefig(filename)
        plt.cla()

    def plot_offset(self,filename):
        plt.plot(self.locs,self.offset,linewidth=1)
        plt.savefig(filename)
        plt.cla()


    def predict(self,dlocs,values):
      observation_pred = self.apply2(dlocs,values)
      return observation_pred


    @staticmethod
    def from_json(data):
        nsigs = len(data['slopes'].keys())
        slopes = []
        for i in range(0,nsigs):
            slopes.append( \
                data['slopes'][str(i)]
            )

        freqs = data['locs']
        offsets = data['offsets']
        return DetLinearXformModel(freqs,slopes,offsets)

    def write(self,filename):
        with open(filename,'w') as fh:
            fh.write(json.dumps(self.to_json()))

    @staticmethod
    def read(filename):
        with open(filename,'r') as fh:
            return DetLinearModel.from_json(json.loads(fh.read()))

class DetNoiseModel(DetLinearModel):

    def __init__(self,freqs,slopes,offsets):
        self.__init__(freqs,slopes,offsets)

    @property
    def freqs(self):
        return self.locs

    def apply_one(self,i,v):
        return self.slope(0)[i]*v + self.offsets[i]

    def apply(self,v):
        return self.slope(0)*v + self.offsets



class DetSignalXform(DetLinearModel):

    def __init__(self,freqs,slopes,offsets,nsamps):
        DetLinearModel.__init__(self,freqs,slopes,offsets,nsamps)

    @property
    def freqs(self):
        return self.locs

    def apply_one(self,i,v):
        pred = self.offset[i] + v
        return pred

    def apply(self,v):
        return self.offset + v


