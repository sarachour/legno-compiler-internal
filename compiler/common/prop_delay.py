import ops.op as op
import ops.nop as nop
import numpy as np
import ops.interval as interval
from compiler.common.visitor_symbolic import SymbolicInferenceVisitor, \
  ExpressionPropagator, PiecewiseSymbolicModel


class DelayPropagator(ExpressionPropagator):

  def __init__(self,env):
    ExpressionPropagator.__init__(self,env)

  def sel(self,m1,m2):
    model = PiecewiseSymbolicModel()
    for cstrs,(u1,v1),(u2,v2) in m1.join(m2):
      u = nop.mksel([u1,u2])
      v = nop.mksel([v1,v2])
      idx = model.add_dist(u,v)
      model.cstrs.add_all(idx,cstrs)

    return model

  def plus(self,m1,m2):
    return self.sel(m1,m2)

  def mult(self,m1,m2):
    return self.sel(m1,m2)

  def integ(self,deriv,ic):
    return self.sel(deriv,ic)

  def const(self,v):
    model = PiecewiseSymbolicModel()
    model.add_expr(nop.mkzero())
    return model

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
