from util.paths import PathHandler
import numpy as np
import compiler.lscale_pass.objective.obj as optlib
import compiler.lscale_pass.scenv as scenvlib

class SlowObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "slow"


  @staticmethod
  def make(circ,jobj,varmap):
    objective = varmap[jobj.scenv.tau()]
    #print(objective)
    if jobj.scenv.uses_tau():
      yield SlowObjFunc(objective)
    else:
      yield SlowObjFunc(0)

class FastObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "fast"


  @staticmethod
  def make(circ,jobj,varmap):
    objective = 1.0/varmap[jobj.scenv.tau()]
    if jobj.scenv.uses_tau():
        yield FastObjFunc(objective)
    else:
        yield FastObjFunc(0)

class FindSCFBoundFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "_findscfbound"

  @staticmethod
  def make(circ,scenv,variable,varmap,minimize=True):
    rngobj = 0.0
    for scvar in scenv.lscale_vars():
      if scenv.lscale_var_in_use(scvar):
         if scenv.get_tag(scvar) == scenvlib.LscaleVarType.SCALE_VAR and \
            variable == scvar:
           if minimize:
             rngobj += varmap[scvar]
           else:
             rngobj += varmap[scvar]**(-1.0)

    yield FindSCFBoundFunc(rngobj)


class NoScaleFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "noscale"

  @staticmethod
  def make(circ,jobj,varmap):
    rngobj = 0.0
    scenv = jobj.scenv
    for scvar in scenv.lscale_vars():
      if scenv.lscale_var_in_use(scvar):
         if scenv.get_tag(scvar) == scenvlib.LscaleVarType.OP_RANGE_VAR:
           rngobj += varmap[scvar]
         elif scenv.get_tag(scvar) == scenvlib.LscaleVarType.SCALE_VAR:
           rngobj += varmap[scvar] + varmap[scvar]**(-1.0)
         #elif scenv.get_tag(scvar) == scenvlib.LscaleVarType.COEFF_VAR:
         #  rngobj += varmap[scvar] + varmap[scvar]**(-1.0)

    yield NoScaleFunc(rngobj)


class MaxSignalObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "maxsig"

  @staticmethod
  def make_mult(scenv,varmap,variables=None):
    rngobj = 0.0
    for scvar in scenv.variables(in_use=True):
      if not (variables is None or scvar in variables):
        continue

      tag = scenv.get_tag(scvar)
      if tag == scenvlib.LscaleVarType.SCALE_VAR:
        rngobj *= 1/varmap[scvar]
    return rngobj

  @staticmethod
  def make_add(scenv,varmap,variables=None):
    rngobj = 0.0
    for scvar in scenv.variables(in_use=True):
      if not (variables is None or scvar in variables):
        continue

      tag = scenv.get_tag(scvar)
      if tag == scenvlib.LScaleVarType.SCALE_VAR:
        rngobj += 1/varmap[scvar]
    return rngobj

  @staticmethod
  def make(circ,jobj,varmap,variables=None):
    scenv = jobj.scenv
    yield MaxSignalObjFunc(MaxSignalObjFunc.make_add(scenv,varmap))
    #if not scenv.solved():
    #  yield MaxSignalObjFunc(MaxSignalObjFunc.make_mult(scenv,varmap))

class MaxSignalAndSpeedObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

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

class MaxSignalAndStabilityObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

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


class MinSignalObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "minsig"

  @staticmethod
  def make_mult(scenv,varmap):
    rngobj = 0.0
    for scvar in scenv.variables(in_use=True):
      tag = scenv.get_tag(scvar)
      if tag == scenvlib.LscaleVarType.SCALE_VAR:
        rngobj *= varmap[scvar]
    return rngobj

  @staticmethod
  def make_add(scenv,varmap):
    rngobj = 0.0
    for scvar in scenv.variables(in_use=True):
      tag = scenv.get_tag(scvar)
      if tag == scenvlib.LscaleVarType.SCALE_VAR:
        rngobj += varmap[scvar]
    return rngobj

  @staticmethod
  def make(circ,jobj,varmap):
    scenv = jobj.scenv
    yield MinSignalObjFunc(MinSignalObjFunc.make_add(scenv,varmap))


def observed(circ,scobj):
  ports = []
  for block_name,loc,config in circ.instances():
    if block_name == 'ext_chip_in':
      continue
    is_measurable = circ.board.handle_by_inst(block_name,loc)
    if not is_measurable is None:
      block = circ.board.block(block_name)
      for port in block.inputs:
        scvar = scobj.scenv.get_scvar(block_name,loc,port,handle=None)
        yield scvar

class FastObsObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "obs" + \
      FastObjFunc.name()

  @staticmethod
  def make(circ,jobj,varmap):
    variables = list(observed(circ,jobj))
    if jobj.time_scaling:
      ot = list(FastObjFunc.make(circ,jobj,varmap))[0]
      for oi in MaxSignalObjFunc.make(circ,jobj,varmap,variables):
        yield FastObsObjFunc(ot.objective()*oi.objective())
    else:
      for obj in MaxSignalObjFunc.make(circ,jobj,varmap,variables):
        yield FastObsObjFunc(obj.objective())

class SlowObsObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "obs" + \
      SlowObjFunc.name()

  @staticmethod
  def make(circ,jobj,varmap):
    variables = list(observed(circ,jobj))
    if jobj.time_scaling:
      ot = list(SlowObjFunc.make(circ,jobj,varmap))[0]
      for oi in MaxSignalObjFunc.make(circ,jobj,varmap,variables):
        yield SlowObsObjFunc(ot.objective()*oi.objective())
    else:
      for obj in MaxSignalObjFunc.make(circ,jobj,varmap,variables):
        yield SlowObsObjFunc(obj.objective())


