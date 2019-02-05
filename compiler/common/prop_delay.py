import ops.op as op
import ops.nop as nop
import numpy as np
import ops.interval as interval
from compiler.common.visitor_symbolic import SymbolicInferenceVisitor, \
  ExpressionPropagator, PiecewiseSymbolicModel


class DelayPropagator(ExpressionPropagator):

  def __init__(self,env):
    ExpressionPropagator.__init__(self,env)

  def max(self,m1,m2):
    model = PiecewiseSymbolicModel()
    for ival,(u1,v1),(u2,v2) in m1.join(m2):
      u = nop.mksel([u1,u2])
      v = nop.mksel([v1,v2])
      model.add_dist(ival,u,v)

    return model

  def plus(self,m1,m2):
    return self.max(m1,m2)

  def mult(self,m1,m2):
    return self.max(m1,m2)

  def integ(self,deriv,ic):
    return self.max(deriv,ic)

  def const(self,v):
    freq_range = interval.Interval.type_infer(0,None)
    model = PiecewiseSymbolicModel()
    model.add_expr(freq_range,nop.mkzero())
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
