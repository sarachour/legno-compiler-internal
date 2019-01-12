import chip.hcdc.util as util

#NOMINAL_NOISE = 1e-9
#NOMINAL_DELAY = 1e-10

DAC_SLACK = 1.0/256
DAC_MIN = util.truncate(-1.0+DAC_SLACK,2)
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
TIME_FREQUENCY = 126000*1.55916665
#TIME_FREQUENCY = 126000.0
# microamps
ANALOG_SLACK = 0.1
ANALOG_MIN = -2.0+ANALOG_SLACK
ANALOG_MAX = 2.0-ANALOG_SLACK
