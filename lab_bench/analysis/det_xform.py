import numpy as np
import json
from sklearn import datasets, linear_model
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
#The following constant was computed in maxima 5.35.1 using 64 bigfloat digits of precision
import math


def find_index_in_sorted_array(array,value):
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or \
                    math.fabs(value - array[idx-1]) \
                    < math.fabs(value - array[idx])):

      loc = idx-1
    else:
      loc = idx

    return loc

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
        self._nsamps = np.array(num_samples)
        self._offsets = np.array(offsets)

    def slope(self,i):
        return self._slopes[i]

    @property
    def offset(self):
        return self._offsets

    def find_nearest_index(self,value):
        return find_index_in_sorted_array(self._locs,value)


    @property
    def num_samples(self):
        return self._nsamps


    @property
    def locs(self):
        return self._locs

    def map_indices(self,values):
        return np.array(list(map(lambda v: \
                        self.find_nearest_index(v),
                        values)))


    def map_locs(self,values):
        return np.array(list(map(lambda v: \
                        self._locs[self.find_nearest_index(v)],
                        values)))

    def apply_one(self,i,value):
        raise NotImplementedError

    def apply(self,values):
        raise NotImplementedError

    def apply2_el(self,loc,value):
      ind = self.find_nearest_index(loc)
      return self.apply_one(ind,value)

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
    # round robin fitting, where each set of elements
    # corresponds to the set of locs given.
    def fit_rr(locs,dep_vars,observations,nsigs):
        # locs is already a unique list
        nlocs = len(locs)
        M = np.zeros((nsigs,nlocs),dtype=float)
        B = np.zeros(nlocs,dtype=float)
        N = np.zeros(nlocs,dtype=int)

        assert(len(set(locs)) == len(locs))

        for dep_var in dep_vars:
          assert(len(dep_var) == len(locs))

        for obs in observations:
          assert(len(obs) == len(locs))


        for idx in range(0,nlocs):
          v = locs[idx]
          xs = list(map(lambda dv: dv[idx],dep_vars))
          ys = list(map(lambda obs: obs[idx],observations))
          if len(xs) == 0:
            continue
          if idx % 1000 == 0:
            print("-> %d/%d" % (idx,nlocs))

          N[idx] = len(ys)
          if nsigs == 0:
            coeff = np.mean(ys)
            B[idx] = coeff

          else:
            regr = linear_model.LinearRegression()
            regr.fit(xs,ys)
            ys_pred = regr.predict(xs)
            error = mean_squared_error(ys, ys_pred)
            for k in range(0,nsigs):
              M[k][idx] = regr.coef_[k]

            B[idx] = regr.intercept_

        return locs,M,B,N


    @staticmethod
    # fitting for unordered sequence of locs, with possible dups.
    # this is acceptable for smaller datasets
    def fit(_locs,_dep_vars,_observations,nsigs):
        inds = np.argsort(_locs)
        locs = _locs[inds]
        print(locs.shape,_locs.shape)
        observations = _observations[inds]
        dep_vars = _dep_vars[inds]
        nlocs = len(np.unique(locs))
        M = np.zeros((nsigs,nlocs),dtype=float)
        B = np.zeros(nlocs,dtype=float)
        L = np.zeros(nlocs,dtype=float)
        N = np.zeros(nlocs,dtype=int)
        i = 0
        idx = 0
        while idx < nlocs:
          # get first different element. otherwise, get end of list
          j = np.argmax(locs>locs[i]) if idx < nlocs-1 \
              else len(locs)-1
          xs = dep_vars[i:j]
          ys = observations[i:j]

          # update locs and N
          L[idx] = locs[i]
          N[idx] = len(ys)

          if idx % 1000 == 0:
            print("-> %d/%d" % (idx,nlocs))
          i=j
          if len(ys) == 0:
            # no slope or offset.
            pass

          elif nsigs == 0 or len(xs) == 0:
            # no slope
            coeff = np.mean(ys)
            B[idx] = coeff

          else:
            # linear model
            regr = linear_model.LinearRegression()
            regr.fit(xs,ys)
            ys_pred = regr.predict(xs)
            error = mean_squared_error(ys, ys_pred)
            for k in range(0,nsigs):
              M[k][idx] = regr.coef_[k]

            B[idx] = regr.intercept_

          idx += 1

        return L,M,B,N

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
    def from_json(cls,data):
        if not 'slopes' in data:
            nsigs = 0
        else:
            nsigs = len(data['slopes'].keys())

        slopes = []
        for i in range(0,nsigs):
            slopes.append( \
                data['slopes'][str(i)]
            )

        freqs = data['locs']
        offsets = data['offsets']
        nsamps = data['num_samples']
        return cls(freqs,slopes,offsets,nsamps)

    def write(self,filename):
        with open(filename,'w') as fh:
            fh.write(json.dumps(self.to_json()))

    @staticmethod
    def read(cls,filename):
        with open(filename,'r') as fh:
            return cls.from_json(json.loads(fh.read()))

class DetNoiseModel(DetLinearModel):

    def __init__(self,freqs,slopes,offsets,nsamps):
        DetLinearModel.__init__(self,freqs,slopes,offsets,nsamps)

    @staticmethod
    def from_json(data):
        return DetLinearModel.from_json(DetNoiseModel,data)

    @staticmethod
    def read(filename):
        return DetLinearModel.read(DetNoiseModel,filename)

    @property
    def freqs(self):
        return self.locs

    def apply_one(self,i,v):
        return self.slope(0)[i]*v + self.offset[i]

    def apply(self,v):
        return self.slope(0)*v + self.offset



class DetSignalXform(DetLinearModel):

    def __init__(self,freqs,slopes,offsets,nsamps):
        DetLinearModel.__init__(self,freqs,slopes,offsets,nsamps)

    @staticmethod
    def from_json(data):
        return DetLinearModel.from_json(DetSignalXform,data)

    @staticmethod
    def read(filename):
        return DetLinearModel.read(DetSignalXform,filename)


    @property
    def values(self):
        return self.locs

    def apply_one(self,i,v):
        pred = self.offset[i] + v
        return pred

    def apply(self,v):
        return self.offset + v


