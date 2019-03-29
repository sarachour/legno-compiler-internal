import ops.op as op
import numpy as np
import ops.interval as interval
from compiler.common.data_symbolic import SymbolicModel
from compiler.common.visitor_symbolic import SymbolicInferenceVisitor
from compiler.common.base_propagator_symbolic import MathPropagator

class PropBiasVisitor(SymbolicInferenceVisitor):

  def __init__(self,circ):
    SymbolicInferenceVisitor.__init__(self,circ,\
                                      MathPropagator)

  def get_generate_expr(self,stump):
    return stump.bias

  def get_propagate_model(self,block_name,loc,port):
    config = self._circ.config(block_name,loc)
    return config.propagated_bias(port)


  def get_generate_model(self,block_name,loc,port):
    config = self._circ.config(block_name,loc)
    return config.generated_bias(port)

  def set_propagate_model(self,block_name,loc,port,gen_model):
    config = self._circ.config(block_name,loc)
    config.set_propagated_bias(port,gen_model)


  def set_generate_model(self,block_name,loc,port,gen_model):
    config = self._circ.config(block_name,loc)
    config.set_generated_bias(port,gen_model)


def compute(circ):
  PropBiasVisitor(circ).all()
