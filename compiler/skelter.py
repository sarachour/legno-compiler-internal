import ops.op as op
import numpy as np
import ops.interval as interval
import compiler.common.evaluator_symbolic as evaluator
import compiler.common.evaluator_heuristic as evalheur
from compiler.common import prop_noise, prop_bias, prop_delay

def compute_snr(nz_eval,circ,block_name,loc,port):
  config = circ.config(block_name,loc)
  scf = config.scf(port)
  signal = config.interval(port).scale(scf)
  noise_mean,noise_var = nz_eval.get(block_name,loc,port)

  if noise_var == 0.0:
    raise Exception("no noise at all?")

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
  for block_name,loc,port in evalheur.get_ports(circ,evaluate=True):
    config = circ.config(block_name,loc)
    signal,noise,snr = compute_snr(nz_eval,circ,block_name,loc,port)
    snrs.append(snr)
    signals.append(signal)
    noises.append(noise)

  snr = np.prod(noises)/np.prod(signals)
  sig = np.prod(list(map(lambda s: 1.0/s, signals)))
  return sum(snrs)
  #return np.min(snrs)*1.0/circ.tau

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
