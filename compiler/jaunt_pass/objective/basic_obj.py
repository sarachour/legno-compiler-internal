from util.paths import PathHandler
import numpy as np
import compiler.jaunt_pass.objective.obj as optlib
import compiler.jaunt_pass.jenv as jenvlib

class SlowObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "slow"


  @staticmethod
  def make(circ,jobj,varmap):
    objective = varmap[jobj.jenv.TAU]
    #print(objective)
    if jobj.jenv.uses_tau():
      yield SlowObjFunc(objective)
    else:
      yield SlowObjFunc(0)

class FastObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "fast"


  @staticmethod
  def make(circ,jobj,varmap):
    objective = 1.0/varmap[jobj.jenv.TAU]
    if jobj.jenv.uses_tau():
        yield FastObjFunc(objective)
    else:
        yield FastObjFunc(0)

class FindSCFBoundFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "_findscfbound"

  @staticmethod
  def make(circ,jenv,variable,varmap,minimize=True):
    rngobj = 0.0
    for scvar in jenv.jaunt_vars():
      if jenv.jaunt_var_in_use(scvar):
         if jenv.get_tag(scvar) == jenvlib.JauntVarType.SCALE_VAR and \
            variable == scvar:
           if minimize:
             rngobj += varmap[scvar]
           else:
             rngobj += varmap[scvar]**(-1.0)

    yield FindSCFBoundFunc(rngobj)


class NoScaleFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "noscale"

  @staticmethod
  def make(circ,jobj,varmap):
    rngobj = 0.0
    jenv = jobj.jenv
    for scvar in jenv.jaunt_vars():
      if jenv.jaunt_var_in_use(scvar):
         if jenv.get_tag(scvar) == jenvlib.JauntVarType.OP_RANGE_VAR:
           rngobj += varmap[scvar]
         elif jenv.get_tag(scvar) == jenvlib.JauntVarType.SCALE_VAR:
           rngobj += varmap[scvar] + varmap[scvar]**(-1.0)
         #elif jenv.get_tag(scvar) == jenvlib.JauntVarType.COEFF_VAR:
         #  rngobj += varmap[scvar] + varmap[scvar]**(-1.0)

    yield NoScaleFunc(rngobj)


class MaxSignalObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "maxsig"

  @staticmethod
  def make(circ,jobj,varmap):
    rngobj = 1.0
    jenv = jobj.jenv
    for scvar in jenv.jaunt_vars():
      if jenv.jaunt_var_in_use(scvar) \
         and jenv.get_tag(scvar) == jenvlib.JauntVarType.SCALE_VAR:
        rngobj += 1.0/varmap[scvar]
    yield MaxSignalObjFunc(rngobj)

class MaxSignalAndSpeedObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return MaxSignalObjFunc.name() + \
      FastObjFunc.name()

  @staticmethod
  def make(circ,jobj,varmap):
    ot = list(FastObjFunc.make(circ,jobj,varmap))[0]
    oi = list(MaxSignalObjFunc.make(circ,jobj,varmap))[0]
    yield MaxSignalAndSpeedObjFunc(ot.objective()*oi.objective())

class MaxSignalAndStabilityObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return MaxSignalObjFunc.name() + \
      SlowObjFunc.name()

  @staticmethod
  def make(circ,jobj,varmap):
    ot = list(SlowObjFunc.make(circ,jobj,varmap))[0]
    oi = list(MaxSignalObjFunc.make(circ,jobj,varmap))[0]
    yield MaxSignalAndStabilityObjFunc(ot.objective()*oi.objective())


class MultSpeedObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj,idx,tau,cstrs):
    self._tau = tau
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
    for obj in SlowObjFunc.make(circ,jobj,varmap):
      yield obj
    for obj in FastObjFunc.make(circ,jobj,varmap):
      yield obj

    jenv = jobj.jenv
    min_t=jobj.result('slow')['freevariables'][jenv.TAU]
    max_t=jobj.result('fast')['freevariables'][jenv.TAU]
    if abs(min_t-max_t) < 1e-6:
      return

    taus = np.logspace(np.log10(min_t),np.log10(max_t),n)
    for idx in range(0,n):
      tau = taus[idx]
      cstrs = [
        varmap[jenv.TAU] <= tau*1.1,
        varmap[jenv.TAU] >= tau*0.9
      ]
      yield cls.mkobj(circ,jobj,varmap,idx,tau,cstrs)

class MaxSignalAtSpeedObjFunc(MultSpeedObjFunc):

  def __init__(self,obj,idx,tau,cstrs):
    MultSpeedObjFunc.__init__(self,obj,idx,tau,cstrs)

  def mktag(self,idx):
    return "sig-tau%d" % idx

  @staticmethod
  def name():
    return "sig-sweep-tau"

  @staticmethod
  def mkobj(circ,jobj,varmap,idx,tau,cstrs):
    obj = list(MaxSignalObjFunc.make(circ,jobj,varmap))[0].objective()
    return MaxSignalAtSpeedObjFunc(obj,
                                   idx=idx,
                                   tau=tau,
                                   cstrs=cstrs)

  @staticmethod
  def make(circ,jobj,varmap,n=7):
    return MultSpeedObjFunc.make(MaxSignalAtSpeedObjFunc,circ, \
                                 jobj,varmap,n=n)
