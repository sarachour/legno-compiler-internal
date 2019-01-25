import ops.op as op
import numpy as np
import ops.interval as interval
import compiler.skelt_pass as skellib

def compute_max_mismatch(circ):
  max_mismatch = 0
  for blkname,loc,config in circ.instances():
    blk = circ.board.block(blkname)
    for port in blk.inputs + blk.outputs:
      mismatches = config.delay_mismatches().values()
      if len(mismatches) > 0:
        max_mismatch = max(max_mismatch,max(mismatches))

  return max_mismatch

def compute_snr(circ,block_name,loc,port):
  config = circ.config(block_name,loc)

  config = circ.config(block_name,loc)
  signal = config.interval(port)
  noise = config.propagated_noise(port)
  bias = config.propagated_bias(port)
  delay = config.propagated_delay(port)

  print("signal: %s" % signal)
  print("noise : %s" % noise)
  print("bias : %s" % bias)
  print("delay : %s" % delay)

  snr = np.log10(signal.difference/(noise.difference+bias.difference))
  return snr

def execute(circ):
  skellib.gen_phys.compute(circ)
  skellib.prop_noise.compute(circ)
  skellib.prop_bias.compute(circ)
  skellib.delay_mismatch.compute(circ)

  score = 0
  max_mismatch = compute_max_mismatch(circ)
  print("mismatch: %s" % max_mismatch)

  # mismatch in seconds
  score += -max_mismatch*1e4
  for handle,block_name,loc in circ.board.handles():
      if circ.in_use(block_name,loc):
        config = circ.config(block_name,loc)
        for port,label,kind in config.labels():
          score += compute_snr(circ,block_name,loc,port)

  return score
