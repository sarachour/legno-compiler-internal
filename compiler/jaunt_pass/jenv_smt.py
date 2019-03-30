import numpy as np
import ops.smtop as smtop
import compiler.jaunt_pass.jaunt_util as jaunt_util
import compiler.jaunt_pass.jenv as jenvlib
import ops.jop as jop
import math

# take logarithm of geometric programming expression.
# for smt expr
def smt_expr(smtenv,expr):
  def recurse(e):
    return smt_expr(smtenv,e)

  if expr.op == jop.JOpType.VAR:
    return smtop.SMTMult(
      smtop.SMTConst(float(expr.exponent)),
      smtop.SMTVar(smtenv.get_smtvar(expr.name))
    )

  if expr.op == jop.JOpType.MULT:
    e1 = recurse(expr.arg(0))
    e2 = recurse(expr.arg(1))
    return smtop.SMTAdd(e1,e2)

  elif expr.op == jop.JOpType.ADD:
    raise Exception("unsupported <%s>" % expr)

  elif expr.op == jop.JOpType.CONST:
    return smtop.SMTConst(math.log10(float(expr.value)))

  else:
    raise Exception("unsupported <%s>" % expr)


def build_smt_prob(circ,jenv,blacklist=[]):
  failed = jenv.failed()
  if failed:
    jaunt_util.log_warn("==== FAIL ====")
    for fail in jenv.failures():
      jaunt_util.log_warn(fail)
    return


  smtenv = smtop.SMTEnv()
  for var in jenv.variables():
    tag = jenv.get_tag(var)
    if tag == jenvlib.JauntVarType.MODE_VAR:
      smtenv.decl(var,smtop.SMTEnv.Type.BOOL)
    elif jenv.jaunt_var_in_use(var):
      smtenv.decl(var,smtop.SMTEnv.Type.REAL)

  constraints = []
  for lhs,rhs,annot in jenv.eqs():
    smt_lhs = smt_expr(smtenv,lhs)
    smt_rhs = smt_expr(smtenv,rhs)
    if not annot in blacklist:
      smtenv.eq(smt_lhs,smt_rhs)

  for lhs,rhs,annot in jenv.ltes():
    smt_lhs = smt_expr(smtenv,lhs)
    smt_rhs = smt_expr(smtenv,rhs)
    if not annot in blacklist:
      smtenv.lte(smt_lhs,smt_rhs)

  if hasattr(jenv,'get_implies'):
    for boolvar,var,value in jenv.get_implies():
      smtboolvar = smtenv.get_smtvar(boolvar)
      smtvar = smtenv.get_smtvar(var)
      smtval = math.log10(value)
      impl = smtop.SMTImplies(
        smtop.SMTVar(smtboolvar),
        smtop.SMTEq(
          smtop.SMTVar(smtvar), \
          smtop.SMTConst(smtval)
        )
      )
      smtenv.cstr(impl)

  if hasattr(jenv,'get_exactly_one'):
    for boolvars in jenv.get_exactly_one():
      smtvars = list(map(lambda bv: smtenv.get_smtvar(bv), boolvars))
      kofn = smtop.SMTExactlyN(smtvars,1)
      smtenv.cstr(kofn)

  if failed:
    print("<< failed >>")
    time.sleep(0.2)
    return

  return smtenv

def solve_smt_prob(smtenv,nslns=1):
  z3ctx = smtenv.to_z3()
  z3ctx.solve()
  if z3ctx.sat():
    yield z3ctx.model()
  else:
    return

  for _ in range(0,nslns-1):
    z3ctx.next_solution()
    if z3ctx.sat():
      yield z3ctx.model()
    else:
      return
