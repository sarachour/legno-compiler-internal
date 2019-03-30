import sys
import os
sys.path.insert(0,os.path.abspath("../../../"))
import chip.phys as phys
import ops.nop as nops
import json
import numpy as np
import chip.hcdc.data.config as cfg


def get_param_scf_weight(blk,scf):
  slack = cfg.data['coeff-mode']['delta']
  if blk == 'adc':
    scfmap = {'10x':'01x','01x':'10x','1x':'1x'}
    scf = scfmap[scf]

  if scf == '10x':
    return (1.0*slack)
  elif scf == '1x':
    return 1.0
  elif '01x':
    return (1.0/slack)

def get_param_rng_weight(blk,scf):
  slack = cfg.data['scale-mode']['delta']
  if blk == 'adc':
    scfmap = {'l':'h','h':'l','m':'m'}
    scf = scfmap[scf]

  whitelist = ['mult','vga','integrator','adc','dac']
  if blk not in whitelist:
    return 1.0

  if scf == 'l':
    return (1.0*slack)
  elif scf == 'm':
    return 1.0
  elif 'h':
    return (1.0*slack)

def get_param_blk_weight(blk):
  baseline = cfg.data['block']['baseline']
  if blk in cfg.data['block']['coeffs']:
    return baseline*cfg.data['block']['coeffs'][blk]
  else:
    return 0.0


def get_param_sig_weight(blk):
  if blk in cfg.data['signal']['weights']:
    for port,weight in cfg.data['signal']['weights'][blk].items():
      yield port,weight
  else:
    return


def get_param_freq_weight(blk):
  #exp = cfg.data['freq']['exponent']
  exp = 1.0
  if blk in cfg.data['freq']['coeffs']:
    return cfg.data['freq']['coeffs'][blk]*cfg.data['freq']['baseline'],exp
  else:
    return 0.0,exp

def get_param_port(blk):
  if blk == 'fanout':
    return 'out0'
  else:
    return 'out'

def mk_noise_model(blk,scf,rng):
  pblk = get_param_blk_weight(blk)
  prng = get_param_rng_weight(blk,rng)
  pscf = get_param_scf_weight(blk,scf)

  wt = pblk*prng*pscf
  terms = []

  pfreq,pfreqexp = get_param_freq_weight(blk)
  port = get_param_port(blk)

  for port,weight in get_param_sig_weight(blk):
    if weight == 0.0:
      continue
    terms.append(nops.mkmult([
      nops.NConstRV(0.0,weight),
      nops.NSig(port)
    ]))

  if wt > 0:
    terms.append(nops.NConstRV(0,wt))
  if pfreq > 0.0:
    terms.append(nops.mkmult([
      nops.NConstRV(0.0,pfreq),
      nops.NFreq(port,power=pfreqexp)
    ]))

  sumexpr = nops.mkadd(terms)
  print(sumexpr)
  return sumexpr

def make_physical_models():
  def mkphys(blk):
    port = get_param_port(blk)
    ph = phys.PhysicalModel(port)
    ph.delay = nops.mkzero()
    ph.noise = nops.mkzero()
    ph.bias = nops.mkzero()
    return ph

  yield 'global_xbar.bb',mkphys('global_xbar')
  yield 'tile_xbar.bb',mkphys('tile_xbar')

  for blk in ['fanout']:
    for rng in ['m','h']:
      filename = "%s-%s.bb" % (blk,rng)
      ph = mkphys(blk)
      ph.noise = mk_noise_model(blk,'1x',rng)
      yield filename,ph

  for blk in ['dac','adc']:
    for rng in ['m','h']:
      filename = "%s-%s.bb" % (blk,rng)
      ph = mkphys(blk)
      if rng == 'm':
        ph.noise = mk_noise_model(blk,'1x',rng)
      else:
        scf = "01x" if 'adc' == blk else '10x'
        ph.noise = mk_noise_model(blk,scf,rng)

      yield filename,ph


  for blk in ['integ','mult','vga']:
    for scf in ['1x','10x','01x']:
      for rng in ['l','m','h']:
        filename = "%s-%s%s.bb" % (blk,rng,scf)
        ph = mkphys(blk)
        ph.noise = mk_noise_model(blk,scf,rng)
        yield filename,ph

for outfile,ph in make_physical_models():
  with open(outfile,'w') as fh:
    obj= ph.to_json()
    objstr = json.dumps(obj,indent=4)
    fh.write(objstr)
