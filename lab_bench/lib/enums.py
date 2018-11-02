from enum import Enum

class BlockType(Enum):
    DAC = 'dac';
    CHIP_INPUT = 'chip_input';
    CHIP_OUTPUT = 'chip_output';
    TILE = "tile"
    MULT = "mult"
    INTEG = "integ"
    FANOUT = "fanout"
    LUT = "lut"

class CircCmdType(Enum):
    USE_DAC = 'use_dac';
    USE_MULT = 'use_mult';
    USE_FANOUT = 'use_fanout';
    USE_INTEG = 'use_integ';
    USE_LUT = 'use_lut';
    DISABLE_DAC = 'use_dac';
    DISABLE_MULT = 'disable_mult';
    DISABLE_INTEG = 'disable_integ';
    DISABLE_FANOUT = 'disable_fanout';
    DISABLE_LUT = 'disable_lut';
    CONNECT = 'connect';
    BREAK = 'break';
    CALIBRATE = 'calibrate';


class ExpCmdType(Enum):
    RESET = 'reset';
    SET_DAC_VALUES = 'set_dac_values';
    GET_ADC_VALUES = 'get_adc_values';
    USE_ANALOG_CHIP = 'use_analog_chip';
    SET_N_ADC_SAMPLES = 'set_n_adc_samples';
    USE_DAC = 'use_dac';
    USE_ADC = 'use_adc';
    USE_OSC = 'use_osc';
    RUN = 'run';

class CmdType(Enum):
    CIRC_CMD = 'circ_cmd';
    EXPERIMENT_CMD = 'exp_cmd';

