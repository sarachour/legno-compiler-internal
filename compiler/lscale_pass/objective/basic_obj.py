from util.paths import PathHandler
import numpy as np
import compiler.lscale_pass.objective.obj as optlib
import compiler.lscale_pass.scenv as scenvlib
import ops.scop as scop

class SlowObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "slow"


  @staticmethod
  def make(circ,jobj):
    objective = jobj.scenv.tau()
    #print(objective)
    if jobj.scenv.uses_tau():
      yield SlowObjFunc(scop.SCVar(objective))
    else:
      yield SlowObjFunc(scop.SCConst(0))

class FastObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "fast"


  @staticmethod
  def make(circ,jobj):
    objective = 1.0/varmap[jobj.scenv.tau()]
    if jobj.scenv.uses_tau():
        yield FastObjFunc(objective)
    else:
        yield FastObjFunc(0)


class MaxSignalObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return "maxsig"

  @staticmethod
  def make_mult(scenv,variables):
    rngobj = scop.SCConst(1.0)
    for scvar in scenv.variables(in_use=True):
      tag = scenv.get_tag(scvar)
      if not variables is None and \
         not scvar in variables:
        continue
      if tag == scenvlib.LScaleVarType.SCALE_VAR:
        term = scop.expo(scop.SCVar(scvar), -1)
        rngobj = scop.SCMult(term,rngobj)
    return rngobj

  @staticmethod
  def make(circ,jobj,variables):
    scenv = jobj.scenv
    yield MaxSignalObjFunc(MaxSignalObjFunc.make_mult(scenv,variables))

class MaxSignalAndSpeedObjFunc(optlib.LScaleObjectiveFunction):

  def __init__(self,obj):
    optlib.LScaleObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return MaxSignalObjFunc.name() + \
      FastObjFunc.name()

  @staticmethod
  def make(circ,jobj):
    if jobj.time_scaling:
      ot = list(FastObjFunc.make(circ,jobj))[0]
      for oi in MaxSignalObjFunc.make(circ,jobj):
        yield MaxSignalAndSpeedObjFunc(scop.SCMult(ot.objective(),oi.objective()))
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
  def make(circ,jobj):
    if jobj.time_scaling:
      ot = list(SlowObjFunc.make(circ,jobj))[0]
      for oi in MaxSignalObjFunc.make(circ,jobj):
        yield MaxSignalAndStabilityObjFunc(scop.SCMult(ot.objective(),oi.objective()))
    else:
      for obj in MaxSignalObjFunc.make(circ,jobj):
        yield obj



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
  def make(circ,jobj):
    variables = list(observed(circ,jobj))
    if jobj.time_scaling:
      ot = list(FastObjFunc.make(circ,jobj))[0]
      for oi in MaxSignalObjFunc.make(circ,jobj,variables):
        yield FastObsObjFunc(scop.SCMult(ot.objective(),oi.objective()))
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
  def make(circ,jobj):
    variables = list(observed(circ,jobj))
    if jobj.time_scaling:
      ot = list(SlowObjFunc.make(circ,jobj))[0]
      for oi in MaxSignalObjFunc.make(circ,jobj,variables):
        yield SlowObsObjFunc(scop.SCMult(ot.objective(),oi.objective()))
    else:
      for obj in MaxSignalObjFunc.make(circ,jobj,variables):
        yield SlowObsObjFunc(obj.objective())


