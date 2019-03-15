import chip.hcdc.util as util
import chip.units as units

#NOMINAL_NOISE = 1e-9
#NOMINAL_DELAY = 1e-10

DAC_SLACK = 1.0/256
DAC_MIN = util.truncate(-1.0,2)
DAC_MAX = util.truncate(1.0-DAC_SLACK,2)
ADC_SAMPLE_US = 3.0
# range for voltage to current
VI_MIN = -0.055
VI_MAX = 0.055
# range for current to voltage
# previously 1.2
IV_MIN = -3.3
IV_MAX = 3.3
# frequency with experimental adjustments
# frequency in kilohz
TIME_FREQUENCY = 20.0*units.khz
#TIME_FREQUENCY = 126000.0
# microamps
ANALOG_SLACK = 0.0
ANALOG_MIN = -2.0+ANALOG_SLACK
ANALOG_MAX = 2.0-ANALOG_SLACK
#ANALOG_MINSIG = 0.15

# minimum value of signal
ANALOG_MINSIG = 0.05
ANALOG_MINSIG_ADC = 0.9

# samples
EXT_DAC_SAMPLES = 4096
ANALOG_DAC_SAMPLES = 256

MIN_QUANT_CONST=8
MIN_QUANT_DYNAMIC=32
MIN_QUANT_EXTIN_DYNAMIC = 256
MIN_QUANT_EXTOUT_DYNAMIC = 64

# maximum frequency for lookup table, in khz
MAX_FREQ = 20.0
MAX_FREQ_LUT = MAX_FREQ
MAX_FREQ_ADC = MAX_FREQ
MAX_FREQ_DAC = MAX_FREQ
