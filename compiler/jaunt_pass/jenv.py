from enum import Enum
import compiler.jaunt_pass.jaunt_util as jaunt_util
import gpkit
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

class JauntEnv:
  TAU = "tau"

  def __init__(self):
    # scaling factor name to port
    self._to_jaunt_var = {}
    self._from_jaunt_var ={}

    self._in_use = {}

    self._eqs = []
    self._ltes = []
    # metavar
    self._meta = {}
    self._metavar = 0
    self._failed = False
    self._failures = []

    self._use_tau = False
    self._solved = False
    self._interactive = False

  def interactive(self):
    self._interactive = True

  def set_solved(self,solved_problem):
      self._solved = solved_problem

  def solved(self):
      return self._solved

  def use_tau(self):
      self._use_tau = True

  def uses_tau(self):
      return self._use_tau

  def fail(self,msg):
      self._failed = True
      self._failures.append(msg)

  def failures(self):
    return self._failures

  def failed(self):
      return self._failed

  def in_use(self,block_name,loc,port,handle=None, \
             tag=JauntVarType.VAR):
      var_name = "%s_%s_%s_%s_%s" % (tag.value,block_name,loc,port,handle)
      return (var_name) in self._in_use

  def jaunt_var_in_use(self,var_name):
      return (var_name) in self._in_use

  def variables(self):
      yield JauntEnv.TAU

      #for tauvar in self._from_tauvar.keys():
      #    yield tauvar

      for scvar in self._from_jaunt_var.keys():
          yield scvar

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

      block_name,loc,port,handle,tag = self._from_jaunt_var[scvar_var]
      return block_name,loc,port,handle,tag

  def get_tag(self,var):
    _,_,_,_,tag = self.get_jaunt_var_info(var)
    return tag

  def jaunt_vars(self):
      return self._from_jaunt_var.keys()

  def get_jaunt_var(self,block_name,loc,port,handle=None, \
                    tag=JauntVarType.VAR):
      key = (block_name,loc,port,handle,tag)
      if not key in self._to_jaunt_var:
          for p in self._to_jaunt_var.keys():
              print(p)
          raise Exception("error: cannot find <%s> in var dict" % str(key))

      scvar = self._to_jaunt_var[key]
      self._in_use[scvar] = True
      return scvar


  def decl_jaunt_var(self,block_name,loc,port,handle=None, \
                     tag=JauntVarType.VAR):
      # create a scaling factor from the variable name
      var_name = "%s_%s_%s_%s_%s" % (tag.value,block_name,loc,port,handle)
      if var_name in self._from_jaunt_var:
          return var_name

      self._from_jaunt_var[var_name] = (block_name,loc,port,handle,tag)
      self._to_jaunt_var[(block_name,loc,port,handle,tag)] = var_name
      return var_name

  def get_inject_var(self,block_name,loc,port,handle=None):
    return self.get_jaunt_var(block_name,loc,port,handle, \
                               tag=JauntVarType.INJECT_VAR)

  def decl_inject_var(self,block_name,loc,port,handle=None):
    return self.decl_jaunt_var(block_name,loc,port,handle, \
                               tag=JauntVarType.INJECT_VAR)

  def has_inject_var(self,block_name,loc,port,handle=None):
    var_name = "%s_%s_%s_%s_%s" % (JauntVarType.INJECT_VAR.value, \
                                   block_name,loc,port,handle)
    return var_name in self._from_jaunt_var

  def get_scvar(self,block_name,loc,port,handle=None):
    return self.get_jaunt_var(block_name,loc,port,handle, \
                               tag=JauntVarType.SCALE_VAR)

  def decl_scvar(self,block_name,loc,port,handle=None):
    return self.decl_jaunt_var(block_name,loc,port,handle, \
                               tag=JauntVarType.SCALE_VAR)


  def eq(self,v1,v2):
      jaunt_util.log_debug("%s == %s" % (v1,v2))
      # TODO: equality
      if self._interactive:
        input()
      self._eqs.append((v1,v2))


  def lte(self,v1,v2):
      jaunt_util.log_debug("%s <= %s" % (v1,v2))
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

    def decl_op_range_var(self,block_name,loc,port,handle=None):
        return self.decl_jaunt_var(block_name,loc,port,handle,
                                   tag=JauntVarType.OP_RANGE_VAR)

    def decl_coeff_var(self,block_name,loc,port,handle=None):
        return self.decl_jaunt_var(block_name,loc,port,handle,
                                   tag=JauntVarType.COEFF_VAR)

    def get_coeff_var(self,block_name,loc,port,handle=None):
        return self.get_jaunt_var(block_name,loc,port,handle,
                                  tag=JauntVarType.COEFF_VAR)

    def get_op_range_var(self,block_name,loc,port,handle=None):
        return self.get_jaunt_var(block_name,loc,port,handle,
                                  tag=JauntVarType.OP_RANGE_VAR)


def gpkit_expr(variables,expr):
    if expr.op == jop.JOpType.VAR:
        return variables[expr.name]**float(expr.exponent)

    elif expr.op == jop.JOpType.MULT:
        e1 = gpkit_expr(variables,expr.arg(0))
        e2 = gpkit_expr(variables,expr.arg(1))
        return e1*e2

    elif expr.op == jop.JOpType.CONST:
        return float(expr.value)

    else:
        raise Exception("unsupported <%s>" % expr)

def build_gpkit_cstrs(circ,jenv):
  failed = jenv.failed()
  if failed:
    jaunt_util.log_warn("==== FAIL ====")
    for fail in jenv.failures():
      jaunt_util.log_warn(fail)
    return


  variables = {}
  for scf in jenv.variables():
      variables[scf] = gpkit.Variable(scf)

  constraints = []
  for orig_lhs,orig_rhs in jenv.eqs():
      succ,lhs,rhs = jaunt_util.cancel_signs(orig_lhs,orig_rhs)
      if not succ:
          print("failed to cancel signs: %s,%s" \
                % (orig_lhs,orig_rhs))
          input()
          failed = True
          continue

      gp_lhs = gpkit_expr(variables,lhs)
      gp_rhs = gpkit_expr(variables,rhs)
      result = (gp_lhs == gp_rhs)
      msg="%s == %s" % (gp_lhs,gp_rhs)
      constraints.append((gp_lhs == gp_rhs,msg))

  for lhs,rhs in jenv.ltes():
      gp_lhs = gpkit_expr(variables,lhs)
      gp_rhs = gpkit_expr(variables,rhs)
      msg="%s <= %s" % (gp_lhs,gp_rhs)
      constraints.append((gp_lhs <= gp_rhs,msg))


  gpkit_cstrs = []
  for cstr,msg in constraints:
      if isinstance(cstr,bool) or isinstance(cstr,np.bool_):
          if not cstr:
              print("[[false]]: %s" % (msg))
              input()
              failed = True
          #else:
          #    print("[[true]]: %s" % (msg))
      else:
          gpkit_cstrs.append(cstr)
          #print("[q] %s" % msg)

  if failed:
      print("<< failed >>")
      time.sleep(0.2)
      return

  cstrs = list(gpkit_cstrs)
  return variables,cstrs

def build_gpkit_problem(circ,jenv,jopt):
  variables,gpkit_cstrs = build_gpkit_cstrs(circ,jenv)
  if gpkit_cstrs is None:
    return

  for obj in jopt.objective(circ,variables):
    cstrs = list(gpkit_cstrs) + list(obj.constraints())
    ofun = obj.objective()
    jaunt_util.log_info(ofun)
    model = gpkit.Model(ofun, cstrs)
    yield model,obj

def solve_gpkit_problem_cvxopt(gpmodel,timeout=10):
    def handle_timeout(signum,frame):
        raise TimeoutError("solver timed out")
    try:
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(timeout)
        sln = gpmodel.solve(solver='cvxopt',verbosity=0)
        signal.alarm(0)
    except RuntimeWarning:
        signal.alarm(0)
        return None
    except TimeoutError as te:
        print("Timeout: cvxopt timed out or hung")
        signal.alarm(0)
        return None

    except ValueError as ve:
        print("ValueError: %s" % ve)
        signal.alarm(0)
        return None

    return sln


def solve_gpkit_problem_mosek(gpmodel,timeout=10):
    def handle_timeout(signum,frame):
        raise TimeoutError("solver timed out")
    try:
        signal.signal(signal.SIGALRM, handle_timeout)
        signal.alarm(timeout)
        sln = gpmodel.solve(solver=CONFIG.GPKIT_SOLVER,
                            warn_on_check=True,
                            verbosity=0)
        signal.alarm(0)
    except TimeoutError as te:
        jaunt_util.log_warn("Timeout: mosek timed out or hung")
        signal.alarm(0)
        return None
    except RuntimeWarning as re:
        jaunt_util.log_warn("[gpkit][ERROR] %s" % re)
        signal.alarm(0)
        return None

    if not 'freevariables' in sln:
      succ,result = sln
      assert(result is None)
      assert(succ == False)
      return None

    return sln


def solve_gpkit_problem(gpmodel,timeout=10):
  if CONFIG.GPKIT_SOLVER == 'cvxopt':
    return solve_gpkit_problem_cvxopt(gpmodel,timeout)
  else:
    return solve_gpkit_problem_mosek(gpmodel,timeout)

def debug_gpkit_problem(gpprob):
  jaunt_util.log_warn(">>> DEBUG <<<")
  gpprob.debug(solver='mosek_cli')
