from enum import Enum

class PortType(Enum):
    PORT_INPUT = 'input';
    PORT_OUTPUT= 'output';

    def code(self):
        if self == PortType.PORT_INPUT:
            return 0
        else:
            return 1

class CodeType(Enum):
    CODE_END = "end"
    CODE_PMOS = "pmos"
    CODE_PMOS2 = "pmos2"
    CODE_NMOS = "nmos"
    CODE_OFFSET = "offset"
    CODE_GAIN_OFFSET = "gain_offset"
    CODE_I2V_OFFSET = "i2v_offset"
    CODE_COMP_LOWER = "comp_lower"
    CODE_COMP_LOWER_FS = "comp_lower_fs"
    CODE_COMP_UPPER = "comp_upper"
    CODE_COMP_UPPER_FS = "comp_upper_fs"

    @staticmethod
    def codes():
        return {
            CodeType.CODE_END:0,
            CodeType.CODE_PMOS:1,
            CodeType.CODE_PMOS2:2,
            CodeType.CODE_NMOS:3,
            CodeType.CODE_OFFSET:4,
            CodeType.CODE_GAIN_OFFSET:5,
            CodeType.CODE_I2V_OFFSET:6,
            CodeType.CODE_COMP_LOWER:7,
            CodeType.CODE_COMP_LOWER_FS:8,
            CodeType.CODE_COMP_UPPER:9,
            CodeType.CODE_COMP_UPPER_FS:10
        }

    @staticmethod
    def from_code(value):
        for code,val in CodeType.codes().items():
            if val == value:
                return code

        raise Exception("no code exists")

class BlockType(Enum):
    DAC = 'dac';
    ADC = 'adc';
    CHIP_INPUT = 'chip_input';
    CHIP_OUTPUT = 'chip_output';
    TILE_INPUT = "tile_input";
    TILE_OUTPUT = "tile_output";
    MULT = "mult";
    INTEG = "integ";
    FANOUT = "fanout";
    LUT = "lut";
    NONE = "<none>";

    def code(self):
        mapping = {
            BlockType.DAC: 0,
            BlockType.MULT: 5,
            BlockType.INTEG: 6,
            BlockType.FANOUT: 7,
            BlockType.LUT: 8,
            BlockType.ADC: 9
        }
        return mapping[self]


class CircCmdType(Enum):
    USE_DAC = 'use_dac';
    USE_MULT = 'use_mult';
    USE_FANOUT = 'use_fanout';
    USE_INTEG = 'use_integ';
    USE_LUT = 'use_lut';
    USE_ADC = 'use_adc';
    DISABLE_DAC = 'disable_dac';
    DISABLE_MULT = 'disable_mult';
    DISABLE_INTEG = 'disable_integ';
    DISABLE_FANOUT = 'disable_fanout';
    DISABLE_LUT = 'disable_lut';
    DISABLE_ADC = 'disable_adc';
    CONNECT = 'connect';
    BREAK = 'break';
    CALIBRATE = 'calibrate';
    GET_INTEG_STATUS = 'get_integ_status';
    GET_ADC_STATUS = 'get_adc_status';
    WRITE_LUT = "write_lut";
    GET_STATE = "get_state";
    SET_STATE = "set_state";
    MEASURE = "measure";
    TUNE = "tune";

class ExpCmdType(Enum):
    RESET = 'reset';
    SET_DAC_VALUES = 'set_dac_values';
    GET_ADC_VALUES = 'get_adc_values';
    GET_OSC_VALUES = 'get_osc_values';
    USE_ANALOG_CHIP = 'use_analog_chip';
    SET_SIM_TIME= 'set_sim_time';
    USE_DAC = 'use_ard_dac';
    USE_ADC = 'use_ard_adc';
    USE_OSC = 'use_osc';
    RUN = 'run';
    COMPUTE_OFFSETS = 'compute_offsets';
    GET_NUM_DAC_SAMPLES = 'get_num_dac_samples';
    GET_NUM_ADC_SAMPLES = 'get_num_adc_samples';
    GET_TIME_BETWEEN_SAMPLES = 'get_time_between_samples';

class CmdType(Enum):
    CIRC_CMD = 'circ_cmd';
    EXPERIMENT_CMD = 'exp_cmd';
    FLUSH_CMD = 'flush_cmd';
