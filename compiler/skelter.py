import ops.op as op
import numpy as np
import ops.interval as interval
import compiler.common.evaluator_symbolic as evaluator
import compiler.common.evaluator_heuristic as evalheur
from compiler.common import prop_noise, prop_bias, prop_delay

def compute_snr(nz_eval,circ,block_name,loc,port):
  config = circ.config(block_name,loc)

  config = circ.config(block_name,loc)
  scf = config.scf(port)
  signal = config.interval(port).scale(scf)
  noise_mean,noise_var = nz_eval.get(block_name,loc,port)

  if noise_var == 0:
    return 100

  snr = signal.bound/noise_var
  return snr

def snr(circ,block_name,loc,port):
  nz_eval = evaluator.propagated_noise_evaluator(circ)
  return compute_snr(nz_eval,circ,block_name,loc,port)

def rank(circ):
  scores = []
  locs = []
  nz_eval = evaluator.propagated_noise_evaluator(circ)

  # mismatch in seconds
  for block_name,loc,port in evalheur.get_ports(circ):
    config = circ.config(block_name,loc)
    scores.append(compute_snr(nz_eval,circ,block_name,loc,port))
    locs.append((block_name,loc,port))

  idx = np.argmin(scores)
  print("lowest-score: %s" % scores[idx])
  print("lowest-loc: %s" % str(locs[idx]))
  return scores[idx]

def clear(circ):
  for _,_,config in circ.instances():
    config.clear_physical_model()

def execute(circ):
  print("<< compute noise >>")
  prop_noise.compute(circ)
  print("<< compute bias >>")
  prop_bias.compute(circ)
  print("<< compute delay >>")
  prop_delay.compute(circ)
