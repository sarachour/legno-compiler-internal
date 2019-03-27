import ops.op as op
import numpy as np
import ops.interval as interval
import compiler.common.evaluator_symbolic as evaluator
import compiler.common.evaluator_heuristic as evalheur
from compiler.common import prop_noise, prop_bias, prop_delay
import math

def compute_snr(nz_eval,circ,block_name,loc,port):
  config = circ.config(block_name,loc)
  if config.interval(port) is None:
    return None,None,None

  scf = config.scf(port)
  signal = config.interval(port).scale(scf)
  noise_mean,noise_var = nz_eval.get(block_name,loc,port)

  if noise_var == 0.0:
    noise_var = 1e-9

  snr = signal.bound/(noise_var)
  return signal.bound,noise_var,snr

def snr(circ,block_name,loc,port):
  nz_eval = evaluator.propagated_noise_evaluator(circ)
  _,nz,snr = compute_snr(nz_eval,circ,block_name,loc,port)
  return snr

def rank_maxsigslow_heuristic(circ):
  score = 0
  for block_name,loc,config in circ.instances():
    block = circ.board.block(block_name)
    for port in block.inputs + block.outputs:
      scf = config.scf(port)
      if scf is None:
        continue

      subscore = ival.scale(scf)/circ.tau
      score += subscore

  return score


def rank_maxsigfast_heuristic(circ):
  score = 0
  for block_name,loc,config in circ.instances():
    block = circ.board.block(block_name)
    for port in block.inputs + block.outputs:
      scf = config.scf(port)
      if scf is None:
        continue

      subscore = scf*circ.tau
      score += subscore

  return score

def rank_model(circ):
  snrs = []
  locs = []
  nz_eval = evaluator.propagated_noise_evaluator(circ)
  # mismatch in seconds
  signals = []
  noises =[]
  for weight,block_name,loc,port in evalheur.get_ports(circ,evaluate=True):
    config = circ.config(block_name,loc)
    signal,noise,snr = compute_snr(nz_eval,circ,block_name,loc,port)
    if not snr is None and snr > 0:
      snrs.append(weight*math.log10(snr))

    if not signal is None:
      signals.append(weight*signal)

    if not noise is None:
      noises.append(weight*noise)

  norm_sigs = list(map(lambda s: s/max(signals), signals))
  if len(noises) == 0:
    return

  max_noises = max(noises)
  if max_noises == 0:
    max_noises = 1e-6

  norm_noises = list(map(lambda s: s/max_noises, signals))
  n = len(signals)
  #score = sum(snrs) + 10.0/circ.tau
  #score = sum(snrs)/circ.tau
  score = sum(snrs)
  print("score= %s" % score)
  for snr,port in zip(snrs, evalheur.get_ports(circ,evaluate=True)):
    print("  %s: %s" % (str(port),snr))
  #return (sum(norm_noises)/n*max(noises))**-1+sum(norm_sigs)/n*max(signals)
  return score

def rank(circ):
  return rank_model(circ)

def clear(circ):
  for _,_,config in circ.instances():
    config.clear_physical_model()

def clear_noise_model(circ):
  for _,_,config in circ.instances():
    config.clear_noise_model()

def execute(circ):
  clear(circ)
  print("<< compute noise >>")
  prop_noise.compute(circ)
  print("<< compute bias >>")
  prop_bias.compute(circ)
  print("<< compute delay >>")
  prop_delay.compute(circ)
  score = rank(circ)
  print("score: %s" % score)
