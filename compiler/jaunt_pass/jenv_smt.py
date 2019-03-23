import numpy as np
import ops.smtop as smtop
import compiler.jaunt_pass.jaunt_util as jaunt_util
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

  elif expr.op == jop.JOpType.CONST:
    return smtop.SMTConst(math.log10(float(expr.value)))

  else:
    raise Exception("unsupported <%s>" % expr)


def build_smt_prob(circ,jenv):
  failed = jenv.failed()
  if failed:
    jaunt_util.log_warn("==== FAIL ====")
    for fail in jenv.failures():
      jaunt_util.log_warn(fail)
    return


  smtenv = smtop.SMTEnv()
  for scf in jenv.variables():
      smtenv.decl(scf,smtop.SMTEnv.Type.REAL)

  constraints = []
  for lhs,rhs in jenv.eqs():
    smt_lhs = smt_expr(smtenv,lhs)
    smt_rhs = smt_expr(smtenv,rhs)
    smtenv.eq(smt_lhs,smt_rhs)

  for lhs,rhs in jenv.ltes():
    smt_lhs = smt_expr(smtenv,lhs)
    smt_rhs = smt_expr(smtenv,rhs)
    smtenv.lte(smt_lhs,smt_rhs)


  if failed:
    print("<< failed >>")
    time.sleep(0.2)
    return

  return smtenv

def solve_smt_prob(smtenv):
  prog = smtenv.to_smtlib2()
  with open('problem.smt2','w') as fh:
    fh.write(prog)
  input("emitted")
