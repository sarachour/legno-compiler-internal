import ops.op as op
import numpy as np
import ops.interval as interval
from compiler.common.visitor import Visitor

class PropBiasVisitor(Visitor):

  def __init__(self,circ):
    Visitor.__init__(self,circ)

  def is_free(self,config,variable):
    return config.propagated_bias(variable) is None

  def input_port(self,block_name,loc,port):
    Visitor.input_port(self,block_name,loc,port)
    circ = self._circ
    config = circ.config(block_name,loc)

    bias = interval.Interval.type_infer(0,0)
    for sblk,sloc,sport in \
      circ.get_conns_by_dest(block_name,loc,port):

      src_bias = circ.config(sblk,sloc).propagated_bias(sport)
      if not src_bias is None:
        bias = bias.add(src_bias)
      else:
        print("[warn] %s[%s].%s has no prop-bias" % \
              (sblk,sloc,sport))

    print("bias in %s[%s].%s = %s" % \
          (block_name,loc,port,bias))
    config.set_propagated_bias(port,bias)


  def output_port(self,block_name,loc,port):
    Visitor.output_port(self,block_name,loc,port)
    circ = self._circ
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    expr = config.dynamics(block,port)

    pbias_dict = dict(config.propagated_biases())
    for var in expr.vars():
      if not var in pbias_dict:
        pbias_dict[var] = interval.Interval.type_infer(0,0)


    # if integral, strip integral sign.
    if expr.op == op.OpType.INTEG:
      prop_bias = expr.deriv.compute_interval(pbias_dict)
    else:
      prop_bias = expr.compute_interval(pbias_dict)

    gen_bias = config.generated_bias(port)
    total_bias = prop_bias.interval.add(gen_bias)
    print("bias out %s[%s].%s = %s" % (block.name,loc,port,total_bias))
    config.set_propagated_bias(port,total_bias)

def compute(circ):
  PropBiasVisitor(circ).toplevel()
