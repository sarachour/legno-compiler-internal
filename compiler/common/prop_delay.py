import ops.op as op
import ops.nop as nop
import numpy as np
import ops.interval as interval
from compiler.common.data_symbolic import SymbolicModel
from compiler.common.visitor_symbolic import SymbolicInferenceVisitor
from compiler.common.propagator_symbolic import ExpressionPropagator


class DelayPropagator(ExpressionPropagator):

  def __init__(self,intbl,outtbl):
    ExpressionPropagator.__init__(self,intbl,outtbl)

  def sel(self,m1,m2):
    u1,v1 = m1.mean,m1.variance
    u2,v2 = m2.mean,m2.variance
    u = nop.mksel([u1,u2])
    v = nop.mksel([v1,v2])
    return SymbolicModel(nop.mkzero(),u,v)

  def sgn(self,m):
    return m

  def rv(self,rv):
    return SymbolicModel(nop.mkzero(),nop.mkconst(rv.mu),nop.mkconst(rv.sigma))



  def cos(self,m):
    return m

  def sin(self,m):
    return m

  def sqrt(self,m):
    return m

  def abs(self,m):
    return m

  def plus(self,m1,m2):
    return self.sel(m1,m2)

  def mult(self,m1,m2):
    return self.sel(m1,m2)

  def integ(self,deriv,ic):
    return self.sel(deriv,ic)

  def const(self,v):
    return SymbolicModel(nop.mkzero(),nop.mkzero(),nop.mkzero())

class PropDelayVisitor(SymbolicInferenceVisitor):

  def __init__(self,circ):
    SymbolicInferenceVisitor.__init__(self,circ,\
                                      DelayPropagator)

  def get_generate_expr(self,stump):
    return stump.delay

  def get_propagate_model(self,block_name,loc,port):
    config = self._circ.config(block_name,loc)
    return config.propagated_delay(port)


  def get_generate_model(self,block_name,loc,port):
    config = self._circ.config(block_name,loc)
    return config.generated_delay(port)

  def set_propagate_model(self,block_name,loc,port,gen_model):
    config = self._circ.config(block_name,loc)
    config.set_propagated_delay(port,gen_model)


  def set_generate_model(self,block_name,loc,port,gen_model):
    config = self._circ.config(block_name,loc)
    config.set_generated_delay(port,gen_model)


def compute(circ):
  PropDelayVisitor(circ).all()
