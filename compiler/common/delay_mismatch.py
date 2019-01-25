import ops.op as op
import numpy as np
import ops.interval as interval
from compiler.common.visitor import Visitor


class PropDelayVisitor(Visitor):

  def __init__(self,circ):
    Visitor.__init__(self,circ)

  def is_free(self,config,variable):
    return config.delay_mismatch(variable) is None or \
      config.propagated_delay(variable) is None


  def compute_propagate(self,delay_list):
    if len(delay_list) == 1:
      return delay_list[0]

    delay = delay_list[0]
    for next_delay in delay_list[1:]:
      delay.union(next_delay)

    return delay

  def compute_mismatch(self,delay_list):
    if len(delay_list) == 1:
      return 0.0

    mismatches = []
    for d1 in delay_list:
      for d2 in delay_list:
        mismatches.append(d1.nonoverlapping(d2))

    return max(mismatches)


  def output_port(self,block_name,loc,port):
    Visitor.output_port(self,block_name,loc,port)
    circ = self._circ
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    expr = config.dynamics(block,port)

    pnz_dict = dict(filter(lambda args: args[0] in expr.vars(), \
                           config.propagated_delays().items()))
    gen_delay = config.generated_delay(port)
    if len(pnz_dict) == 0:
      print("prop-delay %s[%s].%s = %s" % (block_name,loc,port,gen_delay))
      config.set_propagated_delay(port,gen_delay)
    elif len(pnz_dict) > 0:
      propagate_delay = self.compute_propagate(list(pnz_dict.values()))
      mismatch_delay = self.compute_mismatch(list(pnz_dict.values()))
      total_delay = gen_delay.add(propagate_delay)
      print("out prop-delay %s[%s].%s = %s" % (block_name,loc,port,total_delay))
      print("out mismatch %s[%s].%s = %s" % (block_name,loc,port,mismatch_delay))
      config.set_propagated_delay(port,total_delay)
      config.set_delay_mismatch(port,mismatch_delay)


  def input_port(self,block_name,loc,port):
    Visitor.input_port(self,block_name,loc,port)
    circ = self._circ
    config = circ.config(block_name,loc)

    delays = []
    for sblk,sloc,sport in \
      circ.get_conns_by_dest(block_name,loc,port):

      delay = circ.config(sblk,sloc).propagated_delay(sport)
      delays.append(delay)

    if len(delays) > 0:
      mismatch_delay = self.compute_mismatch(delays)
      propagate_delay = self.compute_propagate(delays)
      config.set_propagated_delay(port,propagate_delay)
      config.set_delay_mismatch(port,mismatch_delay)
      print("in prop-delay %s[%s].%s = %s" % (block_name,loc,port,\
                                              propagate_delay))
      print("in mismatch %s[%s].%s = %s" % (block_name,loc,port,mismatch_delay))


def compute(circ):
  PropDelayVisitor(circ).toplevel()
