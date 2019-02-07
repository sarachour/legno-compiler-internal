from lib.enums import BlockType,ExpCmdType,CircCmdType,CmdType
import construct as cstruct

def block_type_t():
    kwargs = {
        BlockType.DAC.name:0,
        BlockType.CHIP_INPUT.name:1,
        BlockType.CHIP_OUTPUT.name:2,
        BlockType.TILE_INPUT.name:3,
        BlockType.TILE_OUTPUT.name:4,
        BlockType.MULT.name:5,
        BlockType.INTEG.name:6,
        BlockType.FANOUT.name:7,
        BlockType.LUT.name:8
    }
    return cstruct.Enum(cstruct.Int16ul,**kwargs)

def experiment_cmd_type_t():
    kwargs = {
        ExpCmdType.RESET.name:0,
        ExpCmdType.SET_DAC_VALUES.name:1,
        ExpCmdType.GET_ADC_VALUES.name:2,
        ExpCmdType.USE_ANALOG_CHIP.name:3,
        ExpCmdType.SET_SIM_TIME.name:4,
        ExpCmdType.USE_DAC.name:5,
        ExpCmdType.USE_ADC.name:6,
        ExpCmdType.USE_OSC.name:7,
        ExpCmdType.RUN.name:8,
        ExpCmdType.COMPUTE_OFFSETS.name:9,
        ExpCmdType.GET_NUM_DAC_SAMPLES.name:10,
        ExpCmdType.GET_TIME_BETWEEN_SAMPLES.name:11,
        ExpCmdType.GET_NUM_ADC_SAMPLES.name:12
    }
    return cstruct.Enum(cstruct.Int16ul,**kwargs)


def circ_cmd_type():
    kwargs = {
        CircCmdType.USE_DAC.name:0,
        CircCmdType.USE_MULT.name:1,
        CircCmdType.USE_FANOUT.name:2,
        CircCmdType.USE_INTEG.name:3,
        CircCmdType.USE_LUT.name:4,
        CircCmdType.USE_ADC.name:5,
        CircCmdType.DISABLE_DAC.name:6,
        CircCmdType.DISABLE_MULT.name:7,
        CircCmdType.DISABLE_INTEG.name:8,
        CircCmdType.DISABLE_FANOUT.name:9,
        CircCmdType.DISABLE_LUT.name:10,
        CircCmdType.CONNECT.name:11,
        CircCmdType.BREAK.name:12,
        CircCmdType.CALIBRATE.name:13,
        CircCmdType.GET_INTEG_STATUS.name:14,
        CircCmdType.GET_ADC_STATUS.name:15,
        CircCmdType.CONFIG_DAC.name:16,
        CircCmdType.CONFIG_MULT.name:17,
        CircCmdType.CONFIG_INTEG.name:18

    }
    return cstruct.Enum(cstruct.Int24ul,
                        **kwargs)


def circ_loc_t():
    return cstruct.Struct(
        "chip"/cstruct.Int8ul,
        "tile"/cstruct.Int8ul,
        "slice"/cstruct.Int8ul,
    )

def circ_loc_idx1_t():
    return cstruct.Struct(
        "loc"/circ_loc_t(),
        "idx"/cstruct.Int8ul,
    )

def circ_loc_idx2_t():
    return cstruct.Struct(
        "idxloc" / circ_loc_idx1_t(),
        "idx2" / cstruct.Int8ul
    )

def circ_use_integ_t():
    return cstruct.Struct(
        "loc" / circ_loc_t(),
        "inv" / cstruct.Int8ul,
        'in_range' / cstruct.Int8ul,
        'out_range' / cstruct.Int8ul,
        'debug' / cstruct.Int8ul,
        cstruct.Padding(1),
        "value" / cstruct.Float32l
    )

def circ_use_dac_t():
    return cstruct.Struct(
        "loc" / circ_loc_t(),
        "source" / cstruct.Int8ul,
        "inv" / cstruct.Int8ul,
        "out_range" / cstruct.Int8ul,
        cstruct.Padding(3),
        "value" / cstruct.Float32l
    )

def circ_use_mult_t():
    return cstruct.Struct(
        "loc" / circ_loc_idx1_t(),
        "use_coeff" / cstruct.Int8ul,
        "in0_range" / cstruct.Int8ul,
        "in1_range" / cstruct.Int8ul,
        "out_range" / cstruct.Int8ul,
        "coeff" / cstruct.Float32l
    )

def circ_use_lut_t():
    return cstruct.Struct(
        "loc" / circ_loc_t(),
        "source" / cstruct.Int8ul
    )

def circ_use_adc_t():
    return cstruct.Struct(
        "loc" / circ_loc_t(),
        "in_range" / cstruct.Int8ul
    )

def circ_use_fanout_t():
    return cstruct.Struct(
        "loc" / circ_loc_idx1_t(),
        "inv" / cstruct.Array(3,cstruct.Int8ul),
        "in_range" / cstruct.Int8ul
    )

def circ_connection_t():
    return cstruct.Struct(
        "src_blk" / block_type_t(),
        "src_loc" / circ_loc_idx2_t(),
        cstruct.Padding(1),
        "dst_blk" / block_type_t(),
        "dst_loc" / circ_loc_idx2_t()
    )


def circ_cmd_data():
    return cstruct.Union(None,
        circ_loc=circ_loc_t(),
        circ_loc_idx1=circ_loc_idx1_t(),
        circ_loc_idx2=circ_loc_idx2_t(),
        fanout=circ_use_fanout_t(),
        integ=circ_use_integ_t(),
        mult=circ_use_mult_t(),
        dac=circ_use_dac_t(),
        lut=circ_use_lut_t(),
        adc=circ_use_adc_t(),
        conn=circ_connection_t()
    )

def circ_cmd_t():
        return cstruct.Struct(
            "type" / circ_cmd_type(),
            cstruct.Padding(1),
            "data" / circ_cmd_data()
        )

def exp_cmd_args_t():
    return cstruct.Union(None,
        floats=cstruct.Array(3,cstruct.Float32l),
        ints=cstruct.Array(3,cstruct.Int32ul)
    )

def experiment_cmd_t():
        typ = experiment_cmd_type_t()
        return cstruct.AlignedStruct(4,
            "type" / typ,
            "args" / exp_cmd_args_t()
        )

def cmd_type_t():
    kwargs = {
        CmdType.CIRC_CMD.name:0,
        CmdType.EXPERIMENT_CMD.name:1,
        CmdType.FLUSH_CMD.name:2
    }
    return cstruct.Enum(cstruct.Int8ul,**kwargs)

def cmd_data_t():
    return cstruct.Union(None,
        "exp_cmd"/ experiment_cmd_t(),
        "circ_cmd" / circ_cmd_t(),
        "flush_cmd" / cstruct.Int8ul
    )


def cmd_t():
    return cstruct.Struct(
        "test" / cstruct.Int8ul,
        "type" / cmd_type_t(),
        cstruct.Padding(2),
        "data" / cmd_data_t(),
        cstruct.Padding(4)
    )
#
