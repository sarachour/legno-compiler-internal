import numpy as np
import ops.smtop as smtop
import compiler.lscale_pass.lscale_util as lscale_util
import compiler.lscale_pass.scenv as scenvlib
import ops.scop as scop
import math

# take logarithm of geometric programming expression.
# for smt expr
def smt_expr(smtenv,expr):
  def recurse(e):
    return smt_expr(smtenv,e)

  if expr.op == scop.SCOpType.VAR:
    return smtop.SMTMult(
      smtop.SMTConst(float(expr.exponent)),
      smtop.SMTVar(smtenv.get_smtvar(expr.name))
    )

  if expr.op == scop.SCOpType.MULT:
    e1 = recurse(expr.arg(0))
    e2 = recurse(expr.arg(1))
    return smtop.SMTAdd(e1,e2)

  elif expr.op == scop.SCOpType.ADD:
    raise Exception("unsupported <%s>" % expr)

  elif expr.op == scop.SCOpType.CONST:
    return smtop.SMTConst(math.log10(float(expr.value)))

  else:
    raise Exception("unsupported <%s>" % expr)


def build_smt_prob(circ,scenv,blacklist=[]):
  failed = scenv.failed()
  if failed:
    jaunt_util.log_warn("==== FAIL ====")
    for fail in scenv.failures():
      jaunt_util.log_warn(fail)
    return


  smtenv = smtop.SMTEnv()
  for var in scenv.variables():
    tag = scenv.get_tag(var)
    if tag == scenvlib.LScaleVarType.MODE_VAR:
      smtenv.decl(var,smtop.SMTEnv.Type.BOOL)
    else:
      smtenv.decl(var,smtop.SMTEnv.Type.REAL)

  constraints = []
  for lhs,rhs,annot in scenv.eqs():
    smt_lhs = smt_expr(smtenv,lhs)
    smt_rhs = smt_expr(smtenv,rhs)
    if not annot in blacklist:
      smtenv.eq(smt_lhs,smt_rhs)

  for lhs,rhs,annot in scenv.ltes():
    smt_lhs = smt_expr(smtenv,lhs)
    smt_rhs = smt_expr(smtenv,rhs)
    if not annot in blacklist:
      smtenv.lte(smt_lhs,smt_rhs)

  if hasattr(scenv,'get_lts'):
    for lhs,rhs,annot in scenv.get_lts():
      smt_lhs = smt_expr(smtenv,lhs)
      smt_rhs = smt_expr(smtenv,rhs)
      if not annot in blacklist:
        smtenv.lt(smt_lhs,smt_rhs)

  if hasattr(scenv,'get_implies'):
    for boolvar,var,value in scenv.get_implies():
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

  if hasattr(scenv,'get_exactly_one'):
    for boolvars in scenv.get_exactly_one():
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
