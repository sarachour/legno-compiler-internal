import ops.nop as nop
from compiler.common.data_symbolic import SymbolicModel
import ops.op as op

class ExpressionPropagator:

  def __init__(self,insymtbl,outsymtbl):
    self._in = insymtbl
    self._out = outsymtbl

  def mult(self,m1,m2):
    raise NotImplementedError

  def rv(self,c):
    raise NotImplementedError

  def const(self,c):
    raise NotImplementedError

  def plus(self,m1,m2):
    raise NotImplementedError

  def integ(self,m1,m2):
    raise NotImplementedError

  def sqrt(self,m):
    raise NotImplementedError

  def abs(self,m):
    raise NotImplementedError

  def cos(self,m):
    raise NotImplementedError

  def sin(self,m):
    raise NotImplementedError

  def sgn(self,m):
    raise NotImplementedError


  def _get_model(self,port):
    block,loc,_ = self.place
    if self._out.has(block,loc,port):
      model = self._out.get(block,loc,port)
    else:
      model = self._in.get(block,loc,port)
    return model

  def nop_var(self,port):
    model = self._get_model(port)
    return model

  def freq(self,expr):
    s = nop.mkzero()
    u = expr
    v = nop.mkzero()
    return SymbolicModel(s,u,v)

  def sig(self,expr):
    s = nop.mkzero()
    u = expr
    v = nop.mkzero()
    return SymbolicModel(s,u,v)


  def propagate_nop(self,expr):
    def recurse(e):
      return self.propagate_nop(e)

    if not (isinstance(expr,nop.NOp)):
      raise Exception("not nop: %s" % expr)


    if expr.op == nop.NOpType.SIG:
      model = self.sig(expr)

    elif expr.op == nop.NOpType.FREQ:
      model = self.freq(expr)

    elif expr.op == nop.NOpType.CONST_RV:
      model = self.rv(expr)

    elif expr.op == nop.NOpType.ADD:
      sum_v= recurse(nop.mkzero())
      for term in expr.terms():
        term_v = recurse(term)
        sum_v = self.plus(sum_v,term_v)
      model = sum_v

    elif expr.op == nop.NOpType.MULT:
      sum_v= recurse(nop.mkone())
      for term in expr.terms():
        term_v = recurse(term)
        sum_v = self.mult(sum_v,term_v)
      model = sum_v


    else:
      raise Exception("unimpl: %s" % expr)

    if not isinstance(model,SymbolicModel):
      raise Exception("did not return model: %s" % expr)

    return model

  def propagate_op(self,block,loc,port,expr):
    def recurse(e):
      return self.propagate_op(block,loc,port,e)

    if not (isinstance(expr,op.Op)):
      raise Exception("not op: %s" % expr)

    self.place = (block,loc,port)
    if expr.op == op.OpType.INTEG:
      m1 = recurse(expr.deriv)
      m2 = recurse(expr.init_cond)
      self.expr = expr
      model = self.integ(m1,m2)

    elif expr.op == op.OpType.MULT:
      m1 = recurse(expr.arg1)
      m2 = recurse(expr.arg2)
      self.expr = expr
      model = self.mult(m1,m2)

    elif expr.op == op.OpType.VAR:
      model = self.nop_var(expr.name)

    elif expr.op == op.OpType.CONST:
      self.expr = expr
      model = self.const(expr.value)

    elif expr.op == op.OpType.SGN:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      model = self.sgn(m1)

    elif expr.op == op.OpType.SQRT:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      model = self.sqrt(m1)

    elif expr.op == op.OpType.ABS:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      model = self.abs(m1)


    elif expr.op == op.OpType.COS:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      model = self.cos(m1)


    elif expr.op == op.OpType.SIN:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      model = self.sin(m1)

    else:
      raise Exception("unimplemented: %s" % (expr))

    if not isinstance(model,SymbolicModel):
      raise Exception("did not return model: %s" % expr)

    return model

