import compiler.jaunt_pass.objective.obj as optlib
import compiler.jaunt_pass.objective.basic_obj as boptlib
import compiler.jaunt_pass.jaunt_util as jaunt_util
import ops.jop as jop
import random
import numpy as np

class MultScaleObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj,idx,cstrs):
    self._idx = idx
    optlib.JauntObjectiveFunction.__init__(self,obj,
                                           tag=self.mktag(idx), \
                                           cstrs=cstrs)

  @staticmethod
  def name():
    return "multscale"

  @staticmethod
  def build_weights(varsets,varmap):
    def random_weight():
      return random.random()*100.0

    rand_weights = list(map(lambda _: random_weight(), \
                            range(0,len(varsets))))
    weightmap = {}
    for idx,varset in enumerate(varsets):
      weight = rand_weights[idx]
      for var in varset:
        print("%s = %s" % (varmap[var].key,weight))
        weightmap[varmap[var].key] = weight
        break

    return weightmap

  def unique_solution(jobj,objfun,idx):
    def is_same(sln1,sln2):
      assert(set(sln1.keys()) == set(sln2.keys()))
      tol = 1e-2
      for k,v1 in sln1.items():
        v2 = sln2[k]
        if abs(v1-v2) > tol:
          print("%s: %s != %s" % (k.key,v1,v2))
          return False

      return True

    this_sln = jobj.result(objfun.tag())['freevariables']
    for i in range(0,idx):
      other_sln = jobj.result(objfun.mktag(i))['freevariables']
      if is_same(this_sln,other_sln):
        return False
    return True


  @staticmethod
  def make(cls,circ,jobj,varmap,n=7):
    if not jobj.jenv.uses_tau():
      return

    varsets = jaunt_util.reduce_vars(jobj.jenv)
    print("num agg vars: %d" % len(varsets))
    trnum = lambda i : "tr%d" % i
    filename = circ.filename
    for obj in boptlib.SlowObjFunc.make(circ,jobj,varmap):
      yield obj

    tau=jobj.result('slow')['freevariables'][jobj.jenv.tau()]

    ntries =50
    idx = 0
    for tryno in range(0,ntries):
      weights = MultScaleObjFunc.build_weights(varsets,varmap)
      cstrs = [
        varmap[jobj.jenv.tau()] <= tau*1.1,
        varmap[jobj.jenv.tau()] >= tau*0.9
      ]
      thisobj = cls.mkobj(circ,jobj,varmap,idx,weights,cstrs)
      yield thisobj
      if idx > 0 and \
         MultScaleObjFunc.unique_solution(jobj,thisobj,idx):
        idx += 1
      elif idx == 0:
        idx += 1

      if idx >= n:
        return

class MaxRandomSignalObjFunc(MultScaleObjFunc):

  def __init__(self,obj,idx,cstrs):
    MultScaleObjFunc.__init__(self,obj,idx,cstrs)

  def mktag(self,idx):
    return "sig-rand%d" % idx

  @staticmethod
  def name():
    return "sig-random"

  @staticmethod
  def mkobj(circ,jobj,varmap,idx,weights,cstrs):
    rngobj = 0.0
    jenv = jobj.jenv
    for scvar in jenv.jaunt_vars():
      if jenv.jaunt_var_in_use(scvar):
        var = varmap[scvar]
        if not var.key in weights:
          continue
        weight = weights[var.key]
        rngobj += 1.0/(var**weight)
    return MaxRandomSignalObjFunc(rngobj,idx,cstrs)


  @staticmethod
  def make(circ,jobj,varmap,n=7):
    return MultScaleObjFunc.make(MaxRandomSignalObjFunc,circ, \
                                 jobj,varmap,n=n)


class MultSpeedObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj,idx,cstrs):
    self._idx = idx
    optlib.JauntObjectiveFunction.__init__(self,obj,
                                           tag=self.mktag(idx), \
                                           cstrs=cstrs)

  def mktag(self,idx):
    raise NotImplementedError

  @staticmethod
  def name():
    return "multspeed"

  @staticmethod
  def make(cls,circ,jobj,varmap,n=7):
    if not jobj.jenv.uses_tau():
      return

    trnum = lambda i : "tr%d" % i
    filename = circ.filename
    for obj in boptlib.SlowObjFunc.make(circ,jobj,varmap):
      yield obj
    for obj in boptlib.FastObjFunc.make(circ,jobj,varmap):
      yield obj

    jenv = jobj.jenv
    min_t=jobj.result('slow')['freevariables'][jenv.tau()]
    max_t=jobj.result('fast')['freevariables'][jenv.tau()]
    if abs(min_t-max_t) < 1e-6:
      return

    taus = np.logspace(np.log10(min_t),np.log10(max_t),n)
    for idx in range(0,n):
      tau = taus[idx]
      cstrs = [
        varmap[jenv.tau()] <= tau*1.1,
        varmap[jenv.tau()] >= tau*0.9
      ]
      yield cls.mkobj(circ,jobj,varmap,idx,tau,cstrs)

class TauSweepSigObjFunc(MultSpeedObjFunc):

  def __init__(self,obj,idx,cstrs):
    MultSpeedObjFunc.__init__(self,obj,idx,cstrs)

  def mktag(self,idx):
    return "sig-tau%d" % idx

  @staticmethod
  def name():
    return "sig-sweep-tau"

  @staticmethod
  def mkobj(circ,jobj,varmap,idx,tau,cstrs):
    obj = list(boptlib.MaxSignalObjFunc.make(circ,jobj,varmap))[0].objective()
    return TauSweepSigObjFunc(obj,
                              idx=idx,
                              cstrs=cstrs)

  @staticmethod
  def make(circ,jobj,varmap,n=7):
    return MultSpeedObjFunc.make(TauSweepSigObjFunc,circ, \
                                 jobj,varmap,n=n)
