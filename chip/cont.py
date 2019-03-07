import ops.interval as interval
import ops.op as op
from enum import Enum

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

class CSMOpVar(CSMVar):

  def __init__(self,port,handle=None):
    CSMVar.__init__(self,CSMVar.Type.OPVAR,port,handle=handle)

class CSMCoeffVar(CSMVar):

  def __init__(self,port,handle=None):
    CSMVar.__init__(self,CSMVar.Type.COEFFVAR,port,handle=handle)


class ContinuousScaleModel:

  def __init__(self):
    self._vars = {}
    self._eq = []
    self._to_scm = {}
    self._baseline = None

  def set_baseline(self,bl):
    self._baseline = bl

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
