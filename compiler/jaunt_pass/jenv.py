from enum import Enum
import compiler.jaunt_pass.jaunt_util as jaunt_util
import ops.jop as jop
import numpy as np
import util.config as CONFIG
import signal
import sys

class JauntVarType(Enum):
  SCALE_VAR= "SCV"
  COEFF_VAR = "COV"
  OP_RANGE_VAR = "OPV"
  INJECT_VAR = "IJV"
  VAR = "VAR"
  MODE_VAR = "MODV"
  TAU = "TAU"

class JauntEnv:
  def __init__(self):
    # scaling factor name to port
    self._to_jaunt_var = {}
    self._from_jaunt_var ={}

    self._in_use = {}

    self._eqs = []
    self._ltes = []
    self._failed = False
    self._failures = []

    self._use_tau = False
    self._solved = False
    self._interactive = False
    self.decl_jaunt_var((),JauntVarType.TAU)

  def tau(self):
    return self.to_jaunt_var(JauntVarType.TAU,())

  def interactive(self):
    self._interactive = True

  def set_solved(self,solved_problem):
      self._solved = solved_problem

  def solved(self):
      return self._solved

  def use_tau(self):
      self._in_use[self.tau()] = True

  def uses_tau(self):
    return self._in_use[self.tau()]

  def fail(self,msg):
      self._failed = True
      self._failures.append(msg)

  def failures(self):
    return self._failures

  def failed(self):
      return self._failed

  def in_use(self,tup,tag=JauntVarType.VAR):
    var_name = self.to_jaunt_var(tag,tup)
    return self._in_use[var_name]


  def jaunt_var_in_use(self,var_name):
    return self._in_use[var_name]

  def variables(self,in_use=False):
    for var in self._from_jaunt_var.keys():
      if self.jaunt_var_in_use(var) or not in_use:
        yield var

  def eqs(self):
    for lhs,rhs in self._eqs:
      yield (lhs,rhs)

  def ltes(self):
    for lhs,rhs in self._ltes:
      yield (lhs,rhs)


  def get_jaunt_var_info(self,scvar_var):
    if not scvar_var in self._from_jaunt_var:
      print(self._from_jaunt_var.keys())
      raise Exception("not scaling factor table in <%s>" % scvar_var)

    result = self._from_jaunt_var[scvar_var]
    return result

  def get_tag(self,var):
    result = self.get_jaunt_var_info(var)
    return result[0]

  def jaunt_vars(self):
    return self._from_jaunt_var.keys()

  def get_jaunt_var(self,tup, tag=JauntVarType.VAR):
    varname = self.to_jaunt_var(tag,tup)

    if not varname in self._from_jaunt_var:
      for p in self._from_jaunt_var.keys():
        print("  var: %s" % p)
      raise Exception("error: cannot find <%s> in var dict" % str(varname))

    self._in_use[varname] = True
    return varname

  def to_jaunt_var(self,tag,tup):
    args = [tag.value] + list(tup)
    return "_".join(map(lambda a: str(a), args))

  def decl_jaunt_var(self,tup, \
                     tag=JauntVarType.VAR):
      # create a scaling factor from the variable name
    var_name = self.to_jaunt_var(tag,tup)
    if var_name in self._from_jaunt_var:
      return var_name

    self._from_jaunt_var[var_name] = (tag,tup)
    self._to_jaunt_var[(tag,tup)] = var_name
    self._in_use[var_name] = False
    return var_name

  def get_inject_var(self,block_name,loc,port,handle=None):
    return self.get_jaunt_var((block_name,loc,port,handle), \
                               tag=JauntVarType.INJECT_VAR)

  def decl_inject_var(self,block_name,loc,port,handle=None):
    return self.decl_jaunt_var((block_name,loc,port,handle), \
                               tag=JauntVarType.INJECT_VAR)

  def has_inject_var(self,block_name,loc,port,handle=None):
    var_name =self.to_jaunt_var(JauntVarType.INJECT_VAR,
                                (block_name,loc,port,handle))
    return var_name in self._from_jaunt_var

  def get_scvar(self,block_name,loc,port,handle=None):
    return self.get_jaunt_var((block_name,loc,port,handle), \
                              tag=JauntVarType.SCALE_VAR)

  def decl_scvar(self,block_name,loc,port,handle=None):
    return self.decl_jaunt_var((block_name,loc,port,handle), \
                              tag=JauntVarType.SCALE_VAR)


  def eq(self,v1,v2):
      jaunt_util.log_debug("%s == %s" % (v1,v2))
      # TODO: equality
      if self._interactive:
        input()
      succ,lhs,rhs = jaunt_util.cancel_signs(v1,v2)
      if not succ:
        self.fail("could not cancel signs: %s == %s" % (v1,v2))
      self._eqs.append((lhs,rhs))


  def lte(self,v1,v2):
      jaunt_util.log_debug("%s <= %s" % (v1,v2))
      c1,_ = v1.factor_const()
      c2,_ = v2.factor_const()
      if c1 == 0 and c2 >= 0:
        return
      if c2 == 0 and c1 > 0:
        self.fail("trivially false: %s <= %s" % (v1,v2))

      # TODO: equality
      if self._interactive:
        input()
      self._ltes.append((v1,v2))


  def gte(self,v1,v2):
      # TODO: equality
      self.lte(v2,v1)

class JauntInferEnv(JauntEnv):

    def __init__(self):
      JauntEnv.__init__(self)
      self._exactly_one = []
      self._implies = {}

    def decl_op_range_var(self,block_name,loc,port,handle=None):
      return self.decl_jaunt_var((block_name,loc,port,handle),
                                 tag=JauntVarType.OP_RANGE_VAR)

    def decl_coeff_var(self,block_name,loc,port,handle=None):
      return self.decl_jaunt_var((block_name,loc,port,handle),
                                 tag=JauntVarType.COEFF_VAR)

    def get_coeff_var(self,block_name,loc,port,handle=None):
      return self.get_jaunt_var((block_name,loc,port,handle),
                                tag=JauntVarType.COEFF_VAR)

    def get_op_range_var(self,block_name,loc,port,handle=None):
      return self.get_jaunt_var((block_name,loc,port,handle),
                                tag=JauntVarType.OP_RANGE_VAR)


    def decl_mode_var(self,block_name,loc,mode):
      return self.decl_jaunt_var((block_name,loc,mode),
                          tag=JauntVarType.MODE_VAR)


    def get_mode_var(self,block_name,loc,mode):
      return self.get_jaunt_var((block_name,loc,mode),
                                tag=JauntVarType.MODE_VAR)


    def implies(self,condvar,var,value):
      assert(condvar in self._from_jaunt_var)
      if not condvar in self._implies:
        self._implies[condvar] = []
      self._implies[condvar].append((var,value))

    def exactly_one(self,exclusive):
      if len(exclusive) == 0:
        return

      for v in exclusive:
        assert(v in self._from_jaunt_var)
      self._exactly_one.append(exclusive)

    def get_implies(self):
      for condvar in self._implies:
        for var2,value in self._implies[condvar]:
          yield condvar,var2,value

    def get_exactly_one(self):
      for exclusive in self._exactly_one:
        yield exclusive
