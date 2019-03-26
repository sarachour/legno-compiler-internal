import compiler.jaunt_pass.jenv as jenv
import ops.jop as jop
import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jenv as jenvlib
import numpy as np
import gpkit

import util.config as CONFIG
import signal

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
  constraints = []
  blacklist = []
  for var in jenv.variables(in_use=True):
    gpvar = gpkit.Variable(var)
    variables[var] = gpvar
    #constraints.append((gpvar <= VMAX,""))
    #constraints.append((VMIN <= gpvar,""))

  for lhs,rhs,annot in jenv.eqs():
      gp_lhs = gpkit_expr(variables,lhs)
      gp_rhs = gpkit_expr(variables,rhs)
      result = (gp_lhs == gp_rhs)
      msg="%s == %s" % (gp_lhs,gp_rhs)
      if not annot in blacklist:
        constraints.append((gp_lhs == gp_rhs,msg))

  for lhs,rhs,annot in jenv.ltes():
      gp_lhs = gpkit_expr(variables,lhs)
      gp_rhs = gpkit_expr(variables,rhs)
      msg="%s <= %s" % (gp_lhs,gp_rhs)
      if not annot in blacklist:
        constraints.append((gp_lhs <= gp_rhs,msg))


  gpkit_cstrs = []
  for cstr,msg in constraints:
      if isinstance(cstr,bool) or isinstance(cstr,np.bool_):
          if not cstr:
              print("[[false]]: %s" % (msg))
              input()
              failed = True
          else:
              print("[[true]]: %s" % (msg))
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
                            verbosity=3)
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
      jaunt_util.log_warn("[gpkit][ERROR] no freevariables key in sln")
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
  result = gpprob.debug(solver=CONFIG.GPKIT_SOLVER)
