# performs a parameter search over configs, using empirical data.
import chip.hcdc.data.spec as spec
import shutil
import util.util as util
import random
from scipy import optimize
import json

class GenBBSearch:

    def __init__(self):
      self._varmap = util.flatten(spec.spec)
      self._vars = list(self._varmap.keys())
      self._n = len(self._vars)
      self._bounds = []
      for v in self._vars:
        l,u = self._varmap[v]
        print("[%f,%f]" % (l,u))

        self._bounds.append((l,u))

      # define all input parameters

    def random_value(self, i):
      l,u = self._bounds[i]
      return random.uniform(l,u)

    def random_vect(self):
      return list(map(lambda i: self.random_value(i), range(0,self._n)))

    def evaluate(self,parvect):
      print(parvect)
      data = util.unflatten(dict(zip(self._vars,parvect)))
      clsbody = "data="+json.dumps(data,indent=4)
      print(clsbody)
      input()

    def optimize(self,optfun):
      res = optimize.brute(optfun,
                            self._bounds,
                            full_output=True,
                            Ns=3,
                            finish=optimize.fmin)

      print(res[0])
      print(res[1])

if __name__ == '__main__':
  search = GenBBSearch()

  def optfun(x, *args):
    return search.evaluate(x)

  search.optimize(optfun)
