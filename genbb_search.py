# performs a parameter search over configs, using empirical data.
import chip.hcdc.data.spec as spec
import util.util as util
import scripts.analyze_experiments as analyze
import scripts.visualize.correlation as correlate

import sys
from scipy import optimize
import numpy as np
import random
import json
import os

class GenBBSearch:

  def __init__(self):
    self._varmap = util.flatten(spec.spec)
    self._vars = list(self._varmap.keys())
    self._n = len(self._vars)
    self.population = 10
    self.generations = 100
    self.idx = 0
    self.n = self.population*self.generations*len(self._vars)
    self._bounds = []
    self.logfile = 'optlog.txt'

    for v in self._vars:
      l,u = self._varmap[v]

      self._bounds.append((l,u))

    # define all input parameters

  def random_value(self, i):
    l,u = self._bounds[i]
    return random.uniform(l,u)

  def random_vect(self):
    return list(map(lambda i: self.random_value(i), range(0,self._n)))

  def update_config(self,parvect):
    pardict = dict(zip(self._vars,parvect))
    data = util.unflatten(pardict)

    with open('chip/hcdc/data/config.py','w') as fh:
      clsbody = "data="+json.dumps(data,indent=4)
      fh.write(clsbody)

    return pardict

  def evaluate(self,parvect):
    print("=== iteration [%d/%d] {len:%d,pop:%d,gen:%d} ===" % \
          (self.idx,self.n,len(parvect),self.population,self.generations))
    pardict = self.update_config(parvect)
    for k,v in pardict.items():
      print("  %s=%s" % (k,v))

    os.system('./genbb.sh > /dev/null')
    os.system('python3 exp_driver.py analyze --recompute-params')
    # recompute ranks
    corrs = correlate.compute()
    print("\n=== correlations ===")
    result = 0.0
    for bmark,corr in corrs.items():
      print("  %s: %s" % (bmark,corr))
      result += (1-corr)

    score = result
    print("SCORE: %s\n\n" % score)
    self.idx += 1
    with open(self.logfile,'a+') as fh:
      corrstr = json.dumps(corrs)
      paramstr = json.dumps(pardict)
      fh.write("%f\t%s\t%s\n" % (score,corrstr,paramstr))

    return score

  def optimize_brute(self,optfun):
    res = optimize.brute(optfun,
                          self._bounds,
                          full_output=True,
                          Ns=3,
                          finish=optimize.fmin)

    print(res[0])
    print(res[1])

  def optimize_evo(self,optfun):
    self.idx = 0
    res = optimize.differential_evolution(optfun,
                                          bounds=self._bounds,
                                          strategy='best1bin',
                                          #maxiter=1000,
                                          maxiter=self.generations,
                                          #popsize=15,
                                          popsize=self.population,
                                          tol=0.01,
                                          mutation=(0.5,1),
                                          recombination=0.7,
                                          seed=None,
                                          disp=True,
                                          polish=True,
                                          init='latinhypercube',
                                          atol=0)

    pardict = self.update_config(res.x)
    print("==== done [score=%s] ====" % res.fun)
    for k,v in pardict.items():
      print("  %s=%s" % (k,v))


def copy_best(search):
  paramset = {}
  with open(search.logfile,'r') as fh:
    for line in fh:
      args = line.split('\t')
      coeff = float(args[0])
      paramset[coeff] = (json.loads(args[1]), \
                         json.loads(args[2]))

  scores = list(paramset.keys())
  idx = np.argmin(scores)
  coeffs,params = paramset[scores[idx]]
  for bmark,coeff in coeffs.items():
    print("%s = %s" % (bmark,coeff))

  data = util.unflatten(params)
  with open('chip/hcdc/data/config.py','w') as fh:
    clsbody = "data="+json.dumps(data,indent=4)
    fh.write(clsbody)


if __name__ == '__main__':
  search = GenBBSearch()
  def optfun(x, *args):
    return search.evaluate(x)

  mode = sys.argv[1]
  if mode == 'run':
    search.optimize_evo(optfun)
  elif mode == 'best':
    copy_best(search)
  else:
    raise Exception("usage: genbb_search.py <best|run>")
