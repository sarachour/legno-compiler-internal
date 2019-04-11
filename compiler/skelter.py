import ops.op as op
import numpy as np
import ops.interval as interval
import compiler.common.evaluator_symbolic as evaluator
import compiler.common.evaluator_heuristic as evalheur
import compiler.jaunt_pass.jenv as jenvlib
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

  snr = signal.bound/math.sqrt(noise_var)
  return signal.bound,math.sqrt(noise_var),snr

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
      ival = config.interval(port)
      if scf is None:
        continue

      subscore = ival.scale(scf).bound/circ.tau
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


def rank_interval_heuristic(circ):
  subscores = []
  for weight,block_name,loc,port in evalheur.get_ports(circ,evaluate=True):
    config = circ.config(block_name,loc)
    scf = config.scf(port)
    ival = config.interval(port)
    if scf is None:
      continue

    subscores.append(ival.scale(scf).bound/circ.tau)

  return min(subscores)/circ.tau


def rank_scale_heuristic(circ):
  subscores = []
  for weight,block_name,loc,port in evalheur.get_ports(circ,evaluate=True):
    config = circ.config(block_name,loc)
    scf = config.scf(port)
    if scf is None:
      continue

    subscores.append(scf)

  return min(subscores)/circ.tau

def rank_model(circ):
  snrs = []
  iface_snrs = []
  nz_eval = evaluator.propagated_noise_evaluator(circ)
  # mismatch in seconds
  for _,block_name,loc,port in evalheur.get_iface_ports(circ,False,1.0):
    _,_,snr = compute_snr(nz_eval,circ,block_name,loc,port)
    if not snr is None and snr > 0:
      iface_snrs.append(snr)

  for _,block_name,loc,port in evalheur.get_all_ports(circ,True,1.0):
    config = circ.config(block_name,loc)
    _,_,snr = compute_snr(nz_eval,circ,block_name,loc,port)
    if not snr is None and snr > 0:
      snrs.append(snr)

  score = 1.0
  if len(snrs) == 0 or len(iface_snrs) == 0:
    return 0.0

  snrs = [1] if len(snrs) == 0 else snrs
  iface_snrs [1] if len(iface_snrs) == 0 else iface_snrs
  score = np.log10(min(snrs)*min(iface_snrs))
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
