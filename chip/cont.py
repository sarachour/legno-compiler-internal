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
    assert(low <= high)
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
    self._model = model
    self._csmvar = {}
    self._scf = {}
    self._scfrng = {}
    self._mrng = {}
    self._hrng = {}

  @property
  def model(self):
    return self._model

  def scf(self,var):
    return self._scf[var]

  def hw_range(self,var):
    return self._hrng[var]

  def math_range(self,var):
    return self._mrng[var]

  def csmvar(self,var):
    return self._csmvar[var]

  def assign_hw_range(self,var,ival):
    self._hrng[var] =ival


  def assign_math_range(self,var,ival):
    self._mrng[var] =ival

  def scale_range(self,var):
    return self._scfrng[var]

  def scale_ranges(self):
    return self._scfrng

  def assign_scale_range(self,var,scfival):
    self._scfrng[var] = scfival


  def assign_scf(self,var,scf):
    self._scf[var] = scf

  def assign_csmvar(self,var,value):
    self._csmvar[var] = value

  def __repr__(self):
    s = ""
    for v,val in self._csmvar.items():
      s += "csmvar %s=%f {%s}\n" % (v,val,v.interval)

    s += "\n"
    for v,val in self._mrng.items():
      s += "mrng %s=%s\n" % (v,val)
    s += "\n"

    for v,val in self._hrng.items():
      s += "hrng %s=%s\n" % (v,val)
    s += "\n"

    for v,val in self._scf.items():
      s += "scf %s=%s\n" % (v,val)
    s += "\n"

    for v,val in self._scfrng.items():
      s += "scf-rng %s=%s\n" % (v,val)
    s += "\n"


    return s


class ContinuousScaleModel:

  def __init__(self):
    self._vars = {}
    self._lte = []
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

  def lte(self,expr1,expr2):
    self._lte.append((expr1,expr2))

  def ltes(self):
    return self._lte


  def eq(self,expr1,expr2):
    self._eq.append((expr1,expr2))

  def eqs(self):
    return self._eq

  def var(self,name):
    return self._vars[name]

  def add_scale_mode(self,scale_mode,cstrs):
    if (scale_mode in self._scale_modes):
      raise Exception("already in modes: <%s>" % str(scale_mode))
    self._scale_modes[scale_mode] = cstrs

  def validate_scale_mode(self,ctx,cstrs):
    score = 1.0
    for var,cstrval in cstrs:
      if var.type == CSMVar.Type.OPVAR:
        mrng = ctx.math_range(var)
        hrng = ctx.hw_range(var)
        assert(var.handle is None)
        scrng = ctx.scale_range(var.port)
        hrng_sc = hrng.scale(cstrval).scale(1.01)
        mrng_cons = scrng.scale(mrng.bound)
        if not hrng_sc.contains_value(mrng_cons.lower):
          print("-> NO! %s x %s not in %s" % (mrng,scrng,hrng_sc))
          return False,score
        else:
          score *= mrng_cons.intersection(hrng_sc).spread

    for var,cstr in cstrs:
      if var.type == CSMVar.Type.COEFFVAR:
        expr,coeff = cstr
        result = expr.compute_interval(ctx.scale_ranges())
        if coeff.spread > 0:
          if not result.interval.intersection(coeff).spread > 0:
            print("-> NO! %s not in %s [%s] [%s]" % \
                  (coeff,result.interval,expr,ctx.scale_ranges()))

            return False,score
          else:
            score *= result.interval.intersection(coeff).spread
        else:
          if not result.interval.contains_value(coeff.upper):
            print("-> NO! %s not in %s [%s] [%s]" % \
                  (coeff,result.interval,expr,ctx.scale_ranges()))

            return False,score
          else:
            score *= result.interval.add(coeff.negate()).bound

    return True,score

  def scale_mode(self,ctx):
    scores = []
    modes = []
    for scale_mode,cstrs in self._scale_modes.items():
      print(scale_mode)
      succ,score = self.validate_scale_mode(ctx,cstrs)
      if succ:
        modes.append(scale_mode)
        scores.append(score)

    idxs = sorted(range(0,len(scores)), key=lambda i:-scores[i])
    for idx in idxs:
      yield modes[idx]

