import chip.units as units
import lab_bench.lib.chipcmd.data as chipcmd
from scipy import stats

#'adc_1khz':54.0*units.uW,
#'adc_20khz':82*units.uW,
#'dac_1khz':4.6*units.uW,
#'dac_20khz':20*units.uW,

def linear_model(x,y):
  slope,intercept,_,_,stderr = stats.linregress(x,y)
  return slope,intercept

freqs = [1.0*units.khz,20.0*units.khz]
adc_slope,dac_offset = linear_model(freqs, [54.0*units.uW,82.0*units.uW])
dac_slope,adc_offset = linear_model(freqs, [4.6*units.uW,20.0*units.uW])

# per hertz energy increase
FREQ_ENERGY = {
  'adc':adc_slope,
  'dac':dac_slope,
}

# per block energy
BLOCK_ENERGY = {
  'fanout': 37.0*units.uW,
  'integrator': 28.0*units.uW,
  'multiplier': 61.0*units.uW,
  'vga': 49.0*units.uW,
  'tile_adc':adc_offset,
  'tile_dac':dac_offset,
  'ext_chip_in': 0,
  'lut': 20.0*units.uW,
  'ext_chip_out': 0,
  'ext_chip_analog_in':0,
  'tile_in':0,
  'chip_in':0,
  'tile_out':0,
  'chip_out':0,

}

GLOBAL_ENERGY = {
  'analog_leakage':6.7*units.uW,
  'digital_leakage':85.8*units.uW,
}
scf = 0.25
MODE_ENERGY_FACTOR = {
  'high': (1.0+scf),
  'low': (1.0-scf),
  'med': 1.0
}

def nominal_global_energy():
  return GLOBAL_ENERGY['analog_leakage'] + GLOBAL_ENERGY['digital_leakage']

def nominal_block_energy(block,comp_mode):
  if block == 'multiplier' and comp_mode == 'vga':
    nominal = BLOCK_ENERGY['vga']
  elif block == 'multiplier' and comp_mode == 'mult':
    nominal = BLOCK_ENERGY['mult']
  else:
    nominal = BLOCK_ENERGY[block]

  return nominal

def scale_mode_factor(block,scale_mode):
  if 'tile' in block or 'chip' in block:
    return 1.0

  if chipcmd.RangeType.HIGH in scale_mode or \
     scale_mode == chipcmd.RangeType.HIGH:
    return MODE_ENERGY_FACTOR['high']

  elif chipcmd.RangeType.MED in scale_mode or \
       scale_mode == chipcmd.RangeType.MED:
    return MODE_ENERGY_FACTOR['med']

  elif chipcmd.RangeType.LOW in scale_mode or \
       scale_mode == chipcmd.RangeType.LOW:
    return MODE_ENERGY_FACTOR['low']

  else:
    return 1.0

def freq_energy(circ,block,freq_math):
  fmax = freq_math.fmax*circ.board.time_constant
  if block in FREQ_ENERGY:
    slope = FREQ_ENERGY[block]
    print("slope:%s" % slope)
    input()
  else:
    return 0

def compute_energy(circ,runtime):
  energy_figure = nominal_global_energy()
  for block,loc,cfg in circ.instances():
    output = circ.board.block(block).outputs[0]
    nominal = nominal_block_energy(block,cfg.comp_mode)
    scm_factor = scale_mode_factor(block,cfg.scale_mode)
    freq = freq_energy(circ,block,cfg.bandwidth(output))
    energy = nominal*scm_factor+freq
    print('%s[%s]: %s J/s' % (block,loc,energy))
    energy_figure += energy

  print("figure: %s J/s" % energy_figure)
  print("runtime: %s s" % runtime)
  print("energy: %s uJ" % (energy_figure*runtime/units.uJ))
  return energy_figure,energy_figure*runtime
