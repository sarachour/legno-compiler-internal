import ops.op as op
import numpy as np
import ops.interval as interval
from compiler.skelt_pass.visitor import Visitor

class PropNoiseVisitor(Visitor):

  def __init__(self,circ):
    Visitor.__init__(self,circ)

  def is_free(self,config,variable):
    return config.propagated_noise(variable) is None

  def input_port(self,block_name,loc,port):
    Visitor.input_port(self,block_name,loc,port)
    circ = self._circ
    config = circ.config(block_name,loc)

    noise = interval.Interval.type_infer(0,0)
    for sblk,sloc,sport in \
      circ.get_conns_by_dest(block_name,loc,port):

      src_nz = circ.config(sblk,sloc).propagated_noise(sport)
      if not src_nz is None:
        noise = noise.add(src_nz)
      else:
        print("[warn] %s[%s].%s has no prop-noise" % (sblk,sloc,sport))

    print("nz in %s[%s].%s = %s" % (block_name,loc,port,noise))
    config.set_propagated_noise(port,noise)


  def output_port(self,block_name,loc,port):
    Visitor.output_port(self,block_name,loc,port)
    circ = self._circ
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    expr = config.dynamics(block,port)

    pnz_dict = config.propagated_noises()
    for var in expr.vars():
      if not var in pnz_dict:
        pnz_dict[var] = interval.Interval.type_infer(0,0)

    # if integral, strip integral sign.
    if expr.op == op.OpType.INTEG:
      prop_noise = expr.deriv.compute_interval(pnz_dict)
    else:
      prop_noise = expr.compute_interval(pnz_dict)

    gen_noise = config.generated_noise(port)
    total_noise = prop_noise.interval.add(gen_noise)
    print("nz out %s[%s].%s = %s" % (block.name,loc,port,total_noise))
    config.set_propagated_noise(port,total_noise)



def compute(circ):
  PropNoiseVisitor(circ).toplevel()
