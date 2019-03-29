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

HANDTUNED = {
  'micro-osc-quarter':{
    (jenvlib.JauntVarType.TAU,()): (-1,0.7081),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('tile_out','(HDACv2,0,0,0,0)','in')): (1,0.801),
    #(jenvlib.JauntVarType.SCALE_VAR, \
    # ('integrator','(HDACv2,0,0,0,0)','ic')): (1,0.801)

  },
  'cosc':{
    (jenvlib.JauntVarType.TAU,()): (-1,0.8202),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('multiplier','(HDACv2,0,0,0,0)','coeff')): (-1,0.82),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('multiplier','(HDACv2,0,0,1,0)','coeff')): (-1,0.68),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('fanout','(HDACv2,0,0,0,1)','in')): (1,0.60),

  },
  'pend':{
    (jenvlib.JauntVarType.TAU,()): (1,0.39),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('fanout','(HDACv2,0,0,0,0)','in')): (1,0.964),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('ext_chip_out','(HDACv2,0,3,2)','out')): (1,0.968),
  },
  'vanderpol':{
    (jenvlib.JauntVarType.TAU,()): (-1,0.7509),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('integrator','(HDACv2,0,0,0,0)','in')): (-1,0.7494),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('integrator','(HDACv2,0,0,1,0)','in')): (-1,0.67),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('multiplier','(HDACv2,0,0,0,1)','out')): (-1,0.67),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('multiplier','(HDACv2,0,0,2,1)','out')): (-1,0.675)
  },
  'sensor-fanout':{
    (jenvlib.JauntVarType.TAU,()): (-1,0.299),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('ext_chip_out','(HDACv2,0,3,2)','out')): (1,0.73),
  },
  'sensor-dynsys':{
    (jenvlib.JauntVarType.TAU,()): (1,0.30),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('integrator','(HDACv2,0,0,1,0)','ic')): (1,0.71),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('multiplier','(HDACv2,0,0,0,0)','in0')): (1,0.71),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('ext_chip_out','(HDACv2,0,3,2)','out')): (1,0.84)
  },
  'spring':{
    (jenvlib.JauntVarType.TAU,()): (-1,0.61),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('fanout','(HDACv2,0,0,0,0)','in')): (1,0.789),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('ext_chip_out','(HDACv2,0,3,2)','out')): (1,0.789),
    (jenvlib.JauntVarType.SCALE_VAR, \
     ('integrator','(HDACv2,0,0,1,0)','ic')): (1,0.722),


  }
}
def rank_handtuned_heuristic(bmark,circ):
  data = HANDTUNED[bmark]
  score = 1.0
  for (tag,info),(direc,weight) in data.items():
    if tag == jenvlib.JauntVarType.TAU:
      scf = circ.tau
    else:
      (block,loc,port) = info
      config = circ.config(block,loc)
      scf = config.scf(port)
      if scf is None:
        continue

    score += weight*(scf*direc)

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
  locs = []
  nz_eval = evaluator.propagated_noise_evaluator(circ)
  # mismatch in seconds
  signals = []
  noises =[]
  for weight,block_name,loc,port in evalheur.get_ports(circ,evaluate=True):
    config = circ.config(block_name,loc)
    signal,noise,snr = compute_snr(nz_eval,circ,block_name,loc,port)
    if not snr is None and snr > 0:
      snrs.append(weight*snr)

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
  score = min(snrs)/circ.tau
  #score = sum(map(lambda n: 1/n, noises))*(1.0/circ.tau)
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
