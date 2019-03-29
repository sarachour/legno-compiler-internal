import ops.op as op
import ops.nop as nop
import numpy as np
import ops.interval as interval
from compiler.common.data_symbolic import SymbolicModel
from compiler.common.visitor_symbolic import SymbolicInferenceVisitor
from compiler.common.base_propagator_symbolic import MathPropagator
import util.util as util

class PropNoiseVisitor(SymbolicInferenceVisitor):

  def __init__(self,circ):
    SymbolicInferenceVisitor.__init__(self,circ,\
                                      MathPropagator)

  def get_generate_expr(self,stump):
    return stump.noise

  def get_propagate_model(self,block_name,loc,port):
    config = self._circ.config(block_name,loc)
    model = config.propagated_noise(port)
    return model


  def get_generate_model(self,block_name,loc,port):
    config = self._circ.config(block_name,loc)
    gen_nz = config.generated_noise(port)
    return gen_nz


  def set_propagate_model(self,block_name,loc,port,prop_model):
    config = self._circ.config(block_name,loc)
    config.set_propagated_noise(port,prop_model)


  def set_generate_model(self,block_name,loc,port,gen_model):
    config = self._circ.config(block_name,loc)
    config.set_generated_noise(port,gen_model)


def compute(circ):
  fn = lambda : PropNoiseVisitor(circ).all()
  #util.profile(fn)
  fn()
