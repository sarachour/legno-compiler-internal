import chip.units as units
#'adc_1khz':54.0*units.uW,
#'adc_20khz':82*units.uW,
#'dac_1khz':4.6*units.uW,
#'dac_20khz':20*units.uW,

# per hertz energy increase
FREQ_ENERGY = {
  'adc':(82.0*units.uW-54.0*units.uW)/(20.0-1.0),
  'dac':(20*units.uW-4.6*units.uW)/(20.0-1.0)
}

# per block energy
BLOCK_ENERGY = {
  'fanout': 37.0*units.uW,
  'integrator': 28.0*units.uW,
  'multiplier': 61.0*units.uW,
  'vga': 49.0*units.uW,
  'analog_leakage':6.7*units.uW,
  'digital_leakage':85.8*units.uW
  'adc':54.0*units.uW - FREQ_ENERGY['adc'],
  'dac':4.6*units.uW - FREQ_ENERGY['dac']
}

MODE_ENERGY_FACTOR = {
  'high': 2.0,
  'low': 0.5,
  'med': 1.0
}

def compute_energy_consumption(circ):
  for block,loc,cfg in circ.instances():
    print(block,loc,cfg.scale_mode,cfg.comp_mode)
    input()
