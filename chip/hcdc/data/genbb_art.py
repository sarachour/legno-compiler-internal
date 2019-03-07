import sys
import os
sys.path.insert(0,os.path.abspath("../../../"))
import chip.phys as phys
import ops.nop as nops
import json


def get_param_rng_weight(scf):
  if 'l':
    return 0.1
  elif 'm':
    return 0.0
  elif 'h':
    return -0.1


def get_param_scf_weight(scf):
  if '10x':
    return -0.1
  elif '1x':
    return 0.0
  elif '01x':
    return 0.1

def get_param_blk_weight(blk):
  if 'integ':
    return 1.0
  elif 'mult':
    return 1.5
  elif 'vga':
    return 1.0

def get_param_sig_weight(blk):
  if 'mult' or 'vga':
    return 0.02
  else:
    return 0.0


def get_param_freq_weight(blk):
  return 1.0

def get_param_port(blk):
  if blk == 'fanout':
    return 'out0'
  else:
    return 'out'

def mk_noise_model(blk,scf,rng):
  pblk = get_param_blk_weight(blk)
  pscf = get_param_scf_weight(scf)
  prng = get_param_rng_weight(rng)

  wt = pblk + pscf + prng
  psig = get_param_sig_weight(blk)
  pfreq = get_param_freq_weight(blk)
  port = get_param_port(blk)

  nz_freq = pfreq*wt
  nz_sig = psig*wt
  nz = wt

  return nops.mkadd([
    nops.mkmult([
      nops.NConstRV(0.0,nz_freq),
      nops.NFreq(port)
    ]),
    nops.mkmult([
      nops.NConstRV(0,nz_sig),
      nops.NSig(port)
    ]),
    nops.NConstRV(0,nz)
  ])


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
