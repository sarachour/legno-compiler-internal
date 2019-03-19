import chip.hcdc.util as util
import chip.units as units

#NOMINAL_NOISE = 1e-9
#NOMINAL_DELAY = 1e-10

ALLOW_SCALE = True

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
# leave a tiny bit of padding for rounding issues.
ANALOG_SLACK = 0.1
ANALOG_MIN = -2.0+ANALOG_SLACK
ANALOG_MAX = 2.0-ANALOG_SLACK
#ANALOG_MINSIG = 0.15

# samples
EXT_DAC_SAMPLES = 4096
ANALOG_DAC_SAMPLES = 256

# increased
MIN_QUANT_EXTIN_DYNAMIC = 256
MIN_QUANT_EXTOUT_DYNAMIC = 64


MIN_QUANT_CONST=16
MIN_QUANT_CONST_HIGH_FIDELITY=16
MIN_QUANT_DYNAMIC=64
MIN_QUANT_LUT_DYNAMIC=128

# minimum value of signal, for fullscale
ANALOG_MINSIG_CONST = MIN_QUANT_CONST*(1.0/ANALOG_DAC_SAMPLES)*ANALOG_MAX
ANALOG_MINSIG_DYN = (MIN_QUANT_DYNAMIC)*(1.0/ANALOG_DAC_SAMPLES)*ANALOG_MAX


# maximum frequency for lookup table, in khz
MAX_FREQ = 20.0
MAX_FREQ_LUT = MAX_FREQ
MAX_FREQ_ADC = MAX_FREQ
MAX_FREQ_DAC = MAX_FREQ
