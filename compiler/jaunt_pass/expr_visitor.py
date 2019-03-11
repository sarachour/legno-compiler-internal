import ops.jop as jop
import ops.op as ops
import ops.interval as interval


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
    if expr.op == ops.OpType.CONST:
      return self.visit_const(expr)

    elif expr.op == ops.OpType.VAR:
      return self.visit_var(expr)

    elif expr.op == ops.OpType.MULT:
      return self.visit_mult(expr)

    elif expr.op == ops.OpType.SGN:
      return self.visit_sgn(expr)

    elif expr.op == ops.OpType.ABS:
      return self.visit_abs(expr)

    elif expr.op == ops.OpType.SQRT:
      return self.visit_sqrt(expr)

    elif expr.op == ops.OpType.COS:
      return self.visit_cos(expr)

    elif expr.op == ops.OpType.SIN:
      return self.visit_sin(expr)

    elif expr.op == ops.OpType.INTEG:
      return self.visit_integ(expr)

    else:
        raise Exception("unhandled <%s>" % expr)


  def visit_const(self,c):
    raise NotImplementedError

  def visit_var(self,v):
    raise NotImplementedError

  def visit_mult(self,m):
    raise NotImplementedError

  def visit_sgn(self,s):
    raise NotImplementedError

class SCFPropExprVisitor(ExprVisitor):

  def __init__(self,jenv,circ,block,loc,port):
      ExprVisitor.__init__(self,jenv,circ,block,loc,port)

  def coeff(self,handle):
      block,loc = self.block,self.loc
      config = circ.config(block.name,loc)
      coeff = block.coeff(config.comp_mode,config.scale_mode)
      return jop.JConst(coeff)

  def visit_const(self,expr):
      return jop.JConst(1.0)

  def visit_var(self,expr):
      block,loc = self.block,self.loc
      scvar = self.jenv.get_scvar(block.name,loc,expr.name)
      return jop.JVar(scvar)

  def visit_mult(self,expr):
      expr1 = self.visit_expr(expr.arg1)
      expr2 = self.visit_expr(expr.arg2)
      return jop.JMult(expr1,expr2)

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
      jenv.eq(expr, jop.JConst(1.0))
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
      scvar_ic = scvar_state

      coeff_deriv = self.coeff(expr.deriv_handle)
      coeff_state = self.coeff(expr.handle)
      coeff_ic = self.coeff(expr.ic_handle)

      jenv.eq(jop.JMult(scexpr_ic,coeff_ic), \
              scvar_ic)
      jenv.eq(jop.JMult(scexpr_deriv, coeff_deriv), \
              scvar_deriv)

      scexpr_state = jop.JMult(jop.JVar(jenv.TAU, \
                                        exponent=-1), scvar_deriv)

      jenv.eq(jop.JMult(scexpr_state, coeff_state), \
              scvar_state)

      jenv.use_tau()
      return scvar_state

  def visit(self):
      block,loc = self.block,self.loc
      config = self.circ.config(block.name,loc)
      expr = block.get_dynamics(config.comp_mode,self.port)
      scfvar = jop.JVar(self.jenv.get_scvar(block.name,loc,self.port))
      scexpr = self.visit_expr(expr)
      coeffvar = self.coeff(None)
      self.jenv.eq(scfvar,jop.JMult(scexpr,coeffvar))

class SCFLUTPropExprVisitor(SCFPropExprVisitor):

  def __init__(self,jenv,circ,block,loc,port):
      SCFPropExprVisitor.__init__(self,jenv,circ,block,loc,port)

  def coeff_lut_in(self):
      name = jenv.get_scvar(block.name,loc,expr.name, \
                            handle=jenv.LUT_SCF_IN)
      return jop.JVar(name)

  def coeff_lut_out(self):
      name = jenv.get_scvar(block.name,loc,expr.name, \
                            handle=jenv.LUT_SCF_OUT)
      return jop.JVar(name)


  def visit_var(self,expr):
    scvar = jenv.get_scvar(block.name,loc,expr.name)
    prod = jop.JMult(jop.JVar(scvar),self.coeff_lut_in())
    delta = 1e-4
    cstr_in_interval(jenv,prod, \
                    interval.Interval.type_infer(1.0-delta, 1.0+delta),
                    interval.Interval.type_infer(1.0,1.0)
    )
    return jop.JConst(1.0)

  def visit(self):
    scfvar = jop.JVar(jenv.get_scvar(block.name,loc,out))
    coeffvar = jop.JVar(jenv.get_coeff_var(block.name,loc,out))
    config = circ.config(block.name,loc)
    expr = config.expr(out)
    scexpr = jcomlib.cstr_traverse_expr(jenv,circ,block,loc,out,expr)
    compvar = jop.JVar(jenv.get_scvar(block.name,loc,out, \
                                handle=jenv.LUT_SCF_OUT))
    jenv.eq(scfvar, jop.JMult(jop.JMult(self.coeff_lut_out(), \
                                        scexpr),coeffvar))
    return scfvar
