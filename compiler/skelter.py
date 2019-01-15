import ops.op as op
import numpy as np
import ops.interval as interval
import compiler.skelt_pass as skellib

def compute_score(board,circ,block_name,loc,port,noise):
  block = board.block(block_name)
  config = circ.config(block_name,loc)
  scf = config.scf(port)
  label = config.label(port)

  mmin,mmax = circ.interval(label)
  signal_mag = scf*max(abs(mmin),abs(mmax))
  print(signal_mag)
  print(noise)

  score = np.log10(signal_mag/noise)
  if np.isnan(score):
    input()

  return score

def execute(circ):
  skellib.update_config.compute(circ)
  skellib.prop_noise.compute(circ)
  skellib.prop_bias.compute(circ)
  skellib.delay_mismatch.compute(circ)
  raise Exception("unimplemented")
'''
  score = 0
  for block_name,loc,port,label in endpoints:
    print("%s[%s].%s := %s" % (block,loc,port,label))
    this_score = compute_score(board,circ,block_name,loc,port,noise)
    score += this_score
  return score
'''
