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
    objective = varmap[jobj.jenv.tau()]
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
    objective = 1.0/varmap[jobj.jenv.tau()]
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
  def make_mult(jenv,varmap):
    rngobj = 0.0
    for scvar in jenv.variables(in_use=True):
      tag = jenv.get_tag(scvar)
      if tag == jenvlib.JauntVarType.SCALE_VAR:
        rngobj *= 1/varmap[scvar]

  @staticmethod
  def make_add(jenv,varmap):
    rngobj = 0.0
    for scvar in jenv.variables(in_use=True):
      tag = jenv.get_tag(scvar)
      if tag == jenvlib.JauntVarType.SCALE_VAR:
        rngobj += 1/varmap[scvar]

  @staticmethod
  def make(circ,jobj,varmap):
    jenv = jobj.jenv
    yield MaxSignalObjFunc(MaxSignalObjFunc.make_add(jenv,varmap))
    if not jenv.solved():
      yield MaxSignalObjFunc(MaxSignalObjFunc.make_mult(jenv,varmap))

class MaxSignalAndSpeedObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return MaxSignalObjFunc.name() + \
      FastObjFunc.name()

  @staticmethod
  def make(circ,jobj,varmap):
    if jobj.time_scaling:
      ot = list(FastObjFunc.make(circ,jobj,varmap))[0]
      for oi in MaxSignalObjFunc.make(circ,jobj,varmap):
        yield MaxSignalAndSpeedObjFunc(ot.objective()*oi.objective())
    else:
      for obj in MaxSignalObjFunc.make(circ,jobj,varmap):
        yield obj

class MaxSignalAndStabilityObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return MaxSignalObjFunc.name() + \
      SlowObjFunc.name()

  @staticmethod
  def make(circ,jobj,varmap):
    if jobj.time_scaling:
      ot = list(SlowObjFunc.make(circ,jobj,varmap))[0]
      for oi in MaxSignalObjFunc.make(circ,jobj,varmap):
        yield MaxSignalAndStabilityObjFunc(ot.objective()*oi.objective())
    else:
      for obj in MaxSignalObjFunc.make(circ,jobj,varmap):
        yield obj
