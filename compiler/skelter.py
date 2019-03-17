import ops.op as op
import numpy as np
import ops.interval as interval
import compiler.common.evaluator_symbolic as evaluator
import compiler.common.evaluator_heuristic as evalheur
from compiler.common import prop_noise, prop_bias, prop_delay

def compute_snr(nz_eval,circ,block_name,loc,port):
  config = circ.config(block_name,loc)
  if config.interval(port) is None:
    return None,None,None

  scf = config.scf(port)
  signal = config.interval(port).scale(scf)
  noise_mean,noise_var = nz_eval.get(block_name,loc,port)

  if noise_var == 0.0:
    return signal.bound,noise_var,None

  snr = signal.bound/noise_var
  return signal.bound,noise_var,snr

def snr(circ,block_name,loc,port):
  nz_eval = evaluator.propagated_noise_evaluator(circ)
  _,_,snr = compute_snr(nz_eval,circ,block_name,loc,port)
  return snr

def rank(circ):
  snrs = []
  locs = []
  nz_eval = evaluator.propagated_noise_evaluator(circ)
  # mismatch in seconds
  signals = []
  noises =[]
  for weight,block_name,loc,port in evalheur.get_ports(circ,evaluate=True):
    config = circ.config(block_name,loc)
    signal,noise,snr = compute_snr(nz_eval,circ,block_name,loc,port)
    if not snr is None:
      snrs.append(weight*snr)

    if not signal is None:
      signals.append(weight*signal)

    if not noise is None:
      noises.append(weight*noise)

  norm_sigs = list(map(lambda s: s/max(signals), signals))
  norm_noises = list(map(lambda s: s/max(noises), signals))
  n = len(signals)
  #return (sum(norm_noises)/n*max(noises))**-1+sum(norm_sigs)/n*max(signals)
  return sum(snrs)

def clear(circ):
  for _,_,config in circ.instances():
    config.clear_physical_model()

def execute(circ):
  clear(circ)
  print("<< compute noise >>")
  prop_noise.compute(circ)
  print("<< compute bias >>")
  prop_bias.compute(circ)
  print("<< compute delay >>")
  prop_delay.compute(circ)
