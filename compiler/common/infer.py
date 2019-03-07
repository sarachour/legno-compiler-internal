import compiler.common.prop_interval as prop_interval
import compiler.common.prop_interval as prop_op_range
import compiler.common.prop_bandwidth as prop_bandwidth

def clear(circ):
  for block_name,loc,config in circ.instances():
        config.clear_bandwidths()
        config.clear_intervals()

def infer_intervals(prog,circ):
  prop_interval.compute_intervals(prog,circ)

def infer_bandwidths(prog,circ):
  prop_bandwidth.compute(prog,circ)

def infer_op_ranges(prog,circ):
  prop_op_range.compute_op_ranges(prog,circ)
