from util.paths import PathHandler
import numpy as np
import compiler.jaunt_pass.opt as optlib

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
    for scvar in jenv.scvars():
      if jenv.in_use(scvar):
        rngobj *= 1.0/varmap[scvar]
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
    yield MaxSignalAndSpeedObjFunc(ot.objective()+oi.objective())

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
    yield MaxSignalAndStabilityObjFunc(ot.objective()+oi.objective())


class MaxSignalAtSpeedObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj,idx,tau,cstrs):
    self._tau = tau
    self._idx = idx
    optlib.JauntObjectiveFunction.__init__(self,obj,
                                  tag="tau%d" % idx,
                                           cstrs=cstrs)

  @staticmethod
  def name():
    return "multspeed"

  @staticmethod
  def make(circ,jobj,varmap,n=5):
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
    taus = np.linspace(min_t,max_t,n)
    for idx in range(1,n-1):
      tau = taus[idx]
      cstrs = [varmap[jenv.TAU] == tau]
      obj = list(MaxSignalObjFunc.make(circ,jobj,varmap))[0].objective()
      yield MaxSignalAtSpeedObjFunc(obj,
                                    idx=idx,
                                    tau=tau,
                                    cstrs=cstrs)
