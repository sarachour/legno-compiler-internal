import ops.jop as jop
import ops.op as ops
import ops.interval as interval
from chip.model import ModelDB,get_gain,get_variance
from enum import Enum
import compiler.jaunt_pass.jaunt_common as jaunt_common
import compiler.jaunt_pass.jaunt_util as jaunt_util
import logging

class ExprVisitor:

  def __init__(self,jenv,circ,block,loc,port):
    self.jenv = jenv
    self.circ = circ
    self.block = block
    self.loc = loc
    self.port = port

  def visit(self):
    raise NotImplementedError

  def get_coeff(self,handle=None):
    raise NotImplementedError

  def visit_expr(self,expr):
    result = None
    if expr.op == ops.OpType.CONST:
      result = self.visit_const(expr)

    elif expr.op == ops.OpType.VAR:
      result = self.visit_var(expr)

    elif expr.op == ops.OpType.MULT:
      result = self.visit_mult(expr)

    elif expr.op == ops.OpType.SGN:
      result = self.visit_sgn(expr)

    elif expr.op == ops.OpType.ABS:
      result = self.visit_abs(expr)

    elif expr.op == ops.OpType.SQRT:
      result = self.visit_sqrt(expr)

    elif expr.op == ops.OpType.COS:
      result = self.visit_cos(expr)

    elif expr.op == ops.OpType.SIN:
      result = self.visit_sin(expr)

    elif expr.op == ops.OpType.ADD:
      result = self.visit_add(expr)

    elif expr.op == ops.OpType.POW:
      result = self.visit_pow(expr)

    elif expr.op == ops.OpType.INTEG:
      result = self.visit_integ(expr)

    else:
        raise Exception("unhandled <%s>" % expr)

    assert(not result is None)
    return result


  def visit_const(self,c):
    raise NotImplementedError

  def visit_var(self,v):
    raise NotImplementedError

  def visit_pow(self,e):
    raise NotImplementedError

  def visit_add(self,e):
    raise NotImplementedError

  def visit_mult(self,m):
    raise NotImplementedError

  def visit_sgn(self,s):
    raise NotImplementedError

class SCFPropExprVisitor(ExprVisitor):

  def __init__(self,jenv,circ,block,loc,port):
    ExprVisitor.__init__(self,jenv,circ,block,loc,port)
    self.db = ModelDB()


  def coeff(self,handle):
    block,loc,port = self.block,self.loc,self.port
    pars = jaunt_common.get_parameters(self.jenv,self.circ, \
                                       block,loc,port,handle)

    return pars['hw_gain']

  def visit_const(self,expr):
    return jop.JConst(1.0)

  def visit_pow(self,expr):
    expr1 = self.visit_expr(expr.arg(0))
    expr2 = self.visit_expr(expr.arg(1))
    if expr.arg(1).op == ops.OpType.CONST:
      self.jenv.eq(expr2, jop.JConst(1.0), 'expr-visit-pow')
      return jop.expo(expr1, expr.arg(1).value)
    else:
      self.jenv.eq(expr1, jop.JConst(1.0), 'expr-visit-pow')
      self.jenv.eq(expr2, jop.JConst(1.0), 'expr-visit-pow')
      return jop.JConst(1.0)

  def visit_var(self,expr):
    block,loc = self.block,self.loc
    scvar = self.jenv.get_scvar(block.name,loc,expr.name)
    if self.jenv.has_inject_var(block.name,loc,expr.name):
      injvar = self.jenv.get_inject_var(block.name,loc,expr.name)
      expr = jop.JMult(jop.JVar(scvar),jop.JVar(injvar))
      #self.jenv.eq(jop.JVar(injvar), jop.JConst(2.0), 'expr-visit-noscale-in')
      self.jenv.eq(expr, jop.JConst(1.0), 'expr-visit-inj')
      return expr
    else:
      return jop.JVar(scvar)


  def visit_mult(self,expr):
    expr1 = self.visit_expr(expr.arg1)
    expr2 = self.visit_expr(expr.arg2)
    return jop.JMult(expr1,expr2)

  def visit_add(self,expr):
    expr1 = self.visit_expr(expr.arg1)
    expr2 = self.visit_expr(expr.arg2)
    self.jenv.eq(expr1,expr2,'expr-visit-add')
    return expr1

  def visit_sgn(self,expr):
    expr1 = self.visit_expr(expr.arg(0))
    return jop.JConst(1.0)

  def visit_abs(self,expr):
    expr = self.visit_expr(expr.arg(0))
    return expr

  def visit_sqrt(self,expr):
    expr = self.visit_expr(expr.arg(0))
    new_expr = jop.expo(expr,0.5)
    return new_expr

  def visit_cos(self,expr):
    expr = self.visit_expr(expr.arg(0))
    self.jenv.eq(expr, jop.JConst(1.0), 'expr-visit-cos')
    return jop.JConst(1.0)

  def visit_sin(self,expr):
    return self.visit_cos(expr)

  def visit_integ(self,expr):
    jenv = self.jenv
    block,loc,port = self.block,self.loc,self.port
    # config
    scexpr_ic = self.visit_expr(expr.init_cond)
    scexpr_deriv = self.visit_expr(expr.deriv)

    scvar_deriv = jop.JVar(jenv.get_scvar(block.name,loc,port, \
                                          handle=expr.deriv_handle))
    scvar_state = jop.JVar(jenv.get_scvar(block.name,loc,port, \
                                          handle=expr.handle))
    scvar_ic = jop.JVar(jenv.get_scvar(block.name,loc,port, \
                                          handle=expr.ic_handle))
    coeff_deriv = self.coeff(expr.deriv_handle)
    coeff_state = self.coeff(expr.handle)
    coeff_ic = self.coeff(expr.ic_handle)

    #jaunt_util.log_debug("deriv: coeff=%s var=%s" % (coeff_deriv,scvar_deriv))
    #jaunt_util.log_debug("stvar: coeff=%s var=%s" % (coeff_state,scvar_state))
    #jaunt_util.log_debug("ic:    coeff=%s var=%s" % (coeff_ic,scvar_ic))
    #jaunt_util.log_debug("deriv-expr: %s" % scexpr_deriv)
    #jaunt_util.log_debug("ic-expr: %s" % scexpr_ic)
    jenv.eq(jop.JMult(scexpr_ic,coeff_ic), scvar_ic,'expr-visit-integ')
    jenv.eq(scvar_ic, scvar_state,'expr-visit-integ')

    jenv.eq(jop.JMult(scexpr_deriv, coeff_deriv), scvar_deriv, \
            'expr-visit-integ')

    scexpr_state = jop.JMult(jop.JVar(jenv.tau(), \
                                      exponent=-1), scvar_deriv)

    jenv.eq(jop.JMult(scexpr_state, coeff_state),  \
            scvar_state,'expr-visit-integ')

    jenv.use_tau()
    return scvar_state

  def visit(self):
      block,loc = self.block,self.loc
      config = self.circ.config(block.name,loc)
      if not config.has_expr(self.port):
        expr = block.get_dynamics(config.comp_mode,self.port)
      else:
        expr = config.expr(self.port,inject=False)

      lhsexpr = jop.JVar(self.jenv.get_scvar(block.name,loc,self.port))
      rhsexpr = self.visit_expr(expr)
      if self.jenv.has_inject_var(block.name,loc,self.port):
        injvar = self.jenv.get_inject_var(block.name,loc,self.port)
        self.jenv.eq(rhsexpr, jop.JConst(1.0), 'expr-visit-inj')
        #self.jenv.eq(jop.JVar(injvar), jop.JConst(0.5), 'expr-visit-noscale-in')
        rhsexpr = jop.JMult(rhsexpr,jop.JVar(injvar))

      coeffvar = self.coeff(None)
      total_rhsexpr = jop.JMult(rhsexpr,coeffvar)
      self.jenv.eq(lhsexpr,total_rhsexpr, 'expr-visit-out')
