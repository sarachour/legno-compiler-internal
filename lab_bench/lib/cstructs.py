from lib.enums import BlockType,ExpCmdType,CircCmdType,CmdType
import construct as cstruct

def block_type_t():
    kwargs = {
        BlockType.DAC.name:0,
        BlockType.CHIP_INPUT.name:1,
        BlockType.CHIP_OUTPUT.name:2,
        BlockType.TILE.name:3,
        BlockType.MULT.name:4,
        BlockType.INTEG.name:5,
        BlockType.FANOUT.name:6,
        BlockType.LUT.name:7
    }
    return cstruct.Enum(cstruct.Int8ul,**kwargs)

def experiment_cmd_type_t():
    kwargs = {
        ExpCmdType.RESET.name:0,
        ExpCmdType.SET_DAC_VALUES.name:1,
        ExpCmdType.GET_ADC_VALUES.name:2,
        ExpCmdType.USE_ANALOG_CHIP.name:3,
        ExpCmdType.SET_N_ADC_SAMPLES.name:4,
        ExpCmdType.USE_DAC.name:5,
        ExpCmdType.USE_ADC.name:6,
        ExpCmdType.USE_OSC.name:7,
        ExpCmdType.RUN.name:8,
        ExpCmdType.COMPUTE_OFFSETS.name:9
    }
    return cstruct.Enum(cstruct.Int16ul,**kwargs)


def circ_cmd_type():
    kwargs = {
        CircCmdType.USE_DAC.name:0,
        CircCmdType.USE_MULT.name:1,
        CircCmdType.USE_FANOUT.name:2,
        CircCmdType.USE_INTEG.name:3,
        CircCmdType.USE_LUT.name:4,
        CircCmdType.DISABLE_DAC.name:5,
        CircCmdType.DISABLE_MULT.name:6,
        CircCmdType.DISABLE_INTEG.name:7,
        CircCmdType.DISABLE_FANOUT.name:8,
        CircCmdType.DISABLE_LUT.name:9,
        CircCmdType.CONNECT.name:10,
        CircCmdType.BREAK.name:11,
        CircCmdType.CALIBRATE.name:12
    }
    return cstruct.Enum(cstruct.Int8ul,
                        **kwargs)


def circ_loc_t():
    return cstruct.Struct(
        "chip"/cstruct.Int8ul,
        "tile"/cstruct.Int8ul,
        "slice"/cstruct.Int8ul
    )

def circ_loc_idx1_t():
    return cstruct.Struct(
        "loc"/circ_loc_t(),
        "idx"/cstruct.Int8ul
    )

def circ_loc_idx2_t():
    return cstruct.Struct(
        "idxloc" / circ_loc_idx1_t(),
        "idx2" / cstruct.Int8ul
    )

def circ_use_integ_t():
    return cstruct.AlignedStruct(4,
        "loc" / circ_loc_t(),
        "value" / cstruct.Int8ul,
        "inv" / cstruct.Flag
    )

def circ_use_dac_t():
    return cstruct.AlignedStruct(4,
        "loc" / circ_loc_t(),
        "value" / cstruct.Int8ul,
        "inv" / cstruct.Flag
    )

def circ_use_mult_t():
    return cstruct.AlignedStruct(4,
        "loc" / circ_loc_idx1_t(),
        "use_coeff" / cstruct.Flag,
        "coeff" / cstruct.Int8ul,
        "inv" / cstruct.Flag
    )

def circ_use_fanout_t():
    return cstruct.AlignedStruct(4,
        "loc" / circ_loc_idx1_t(),
        "inv" / cstruct.Array(3,cstruct.Flag)
    )

def circ_connection_t():
    return cstruct.Struct(
        "src_blk" / block_type_t(),
        "src_loc" / circ_loc_idx2_t(),
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
        conn=circ_connection_t()
    )

def circ_cmd_t():
        return cstruct.Struct(
            "type" / circ_cmd_type(),
            "data" / circ_cmd_data()
        )

def experiment_cmd_t():
        typ = experiment_cmd_type_t()
        return cstruct.AlignedStruct(4,
            "type" / typ,
            "args" / cstruct.Array(3,cstruct.Int32ul)
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
    return cstruct.AlignedStruct(4,
        "type" / cmd_type_t(),
        "data" / cmd_data_t()
    )