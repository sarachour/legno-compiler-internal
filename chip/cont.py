import ops.interval as interval
import ops.op as ops
from enum import Enum

def equals(csm,variables):
  for idx in range(len(variables)-1):
    last_var = variables[idx-1]
    this_var = variables[idx]
    csm.eq(ops.Var(last_var.varname), ops.Var(this_var.varname))

def set_interval(variables,lo,hi):
  for v in variables:
    v.set_interval(lo,hi)

def decl_out(csm,port,handle=None):
  op = csm.decl_var(CSMOpVar(port,handle=handle))
  coeff = csm.decl_var(CSMCoeffVar(port,handle=handle))
  return op,coeff


def decl_in(csm,port,handle=None):
  op = csm.decl_var(CSMOpVar(port,handle=handle))
  return op

class CSMVar:
  class Type(Enum):
    OPVAR = "opvar"
    COEFFVAR = "coeffvar"

  def __init__(self,typ,port,handle=None):
    self._port = port
    self._handle = handle
    self._type = typ
    self._ival = None

  @property
  def type(self):
    return self._type

  @property
  def handle(self):
    return self._handle

  @property
  def port(self):
    return self._port

  @property
  def interval(self):
    return self._ival

  def set_interval(self,low,high):
    self._ival = interval.Interval.type_infer(low,high)

  @property
  def varname(self):
    return "%s_%s_%s" % (self._type.value,self._port,self._handle)

  def __repr__(self):
    return "[%s]%s:%s" % (self._type,self._port,self._handle)

  def __eq__(self,o):
    return str(o) == str(self) and \
      o.__class__.__name__ == self.__class__.__name__

  def __hash__(self):
    return hash(str(self))

class CSMOpVar(CSMVar):

  def __init__(self,port,handle=None):
    CSMVar.__init__(self,CSMVar.Type.OPVAR,port,handle=handle)

class CSMCoeffVar(CSMVar):

  def __init__(self,port,handle=None):
    CSMVar.__init__(self,CSMVar.Type.COEFFVAR,port,handle=handle)


class ContinuousScaleContext:

  def __init__(self,model):
    self._assigns = {}
    self._model = model

  @property
  def model(self):
    return self._model

  def value(self,var):
    return self._assigns[var]

  def assign(self,var,value):
    self._assigns[var] = value

  def __repr__(self):
    s = ""
    for v,val in self._assigns.items():
      s += "%s=%f\n" % (v,val)
    return s


class ContinuousScaleModel:

  def __init__(self):
    self._vars = {}
    self._eq = []
    self._scale_modes = {}
    self._baseline = None

  def set_baseline(self,bl):
    self._baseline = bl

  @property
  def baseline(self):
    return self._baseline

  def variables(self):
    return self._vars.values()

  def decl_var(self,var):
    self._vars[var.varname] = var
    return var

  def eq(self,expr1,expr2):
    self._eq.append((expr1,expr2))

  def eqs(self):
    return self._eq

  def var(self,name):
    return self._vars[name]

  def add_scale_mode(self,scale_mode,cstrs):
    self._scale_modes[scale_mode] = cstrs

  def scale_mode(self,ctx):
    scm = None
    for this_scm,cstrs in self._scale_modes.items():
      if not scm is None:
        continue

      is_match = True
      for var,rng in cstrs:
        value = ctx.value(var)
        if not rng.contains_value(value):
          is_match = False


      if is_match:
        assert(scm is None)
        scm = this_scm

    assert(not scm is None)
    return scm
