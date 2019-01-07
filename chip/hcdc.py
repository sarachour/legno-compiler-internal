import chip.props as props
import chip.units as units
import ops.op as ops
from chip.block import Block
from chip.board import Board
import lab_bench.lib.chip_command as chipcmd
import itertools

import numpy as np
def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = '{}'.format(f)
    if 'e' in s or 'E' in s:
        return '{0:.{1}f}'.format(f, n)
    i, p, d = s.partition('.')
    return float('.'.join([i, (d+'0'*n)[:n]]))


DAC_SLACK = 1.0/256
DAC_MIN = truncate(-1.0+DAC_SLACK,2)
DAC_MAX = truncate(1.0-DAC_SLACK,2)
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

def make_ana_props(rng,lb,ub):
    assert(lb < ub)
    return props.AnalogProperties() \
                .set_interval(lb*rng.coeff(),
                              ub*rng.coeff(),
                              unit=units.uA)

def make_dig_props(rng,lb,ub,npts=256):
    start = lb*rng.coeff()
    end = ub*rng.coeff()
    hcdcv2_values = np.linspace(start,end,npts)
    info = props.DigitalProperties() \
                .set_values(hcdcv2_values) \
                .set_constant() \
                .check()
    return info

def apply_blacklist(options,blacklist):
    def in_blacklist(opt,blist):
        for entry in blacklist:
            match = True
            for ov,ev in zip(opt,entry):
                if not ev is None and ov != ev:
                    match = False

            if match:
                return True
        return False

    for opt in options:
        if in_blacklist(opt,blacklist):
            continue
        yield opt

def integ_scale_modes(integ):
    opts = [
        chipcmd.SignType.options(),
        chipcmd.RangeType.options(),
        chipcmd.RangeType.options()
    ]
    blacklist = [
        (None,chipcmd.RangeType.LOW,chipcmd.RangeType.HIGH),
        (None,chipcmd.RangeType.HIGH,chipcmd.RangeType.LOW)
    ]
    modes = list(apply_blacklist(itertools.product(*opts),blacklist))
    integ.set_scale_modes("*",modes)
    for mode in modes:
        sign,inrng,outrng = mode
        scf = outrng.coeff()/inrng.coeff()*sign.coeff()
        integ.set_info("*",mode,['in'],make_ana_props(inrng,ANALOG_MIN,ANALOG_MAX))
        integ.set_info("*",mode,["ic"],make_dig_props(chipcmd.RangeType.MED, \
                                                      DAC_MIN,DAC_MAX))
        integ.set_info("*",mode,["out"],make_ana_props(outrng,ANALOG_MIN,ANALOG_MAX),\
                       handle=":z")
        integ.set_info("*",mode,["out"],make_ana_props(outrng,ANALOG_MIN,ANALOG_MAX),\
                       handle=":z'")
        integ.set_info("*",mode,["out"],make_ana_props(outrng,ANALOG_MIN,ANALOG_MAX))
        integ.set_scale_factor("*",mode,"out",scf)


def mult_scale_modes(mult):
    opts_def = [
        chipcmd.RangeType.options(),
        chipcmd.RangeType.options(),
        chipcmd.RangeType.options()
    ]

    opts_vga = [
        chipcmd.RangeType.options(),
        chipcmd.RangeType.options()
    ]
    blacklist_vga = [
        (chipcmd.RangeType.LOW,chipcmd.RangeType.HIGH)
    ]
    blacklist_mult = [
        (chipcmd.RangeType.LOW,chipcmd.RangeType.LOW,chipcmd.RangeType.HIGH),
        (chipcmd.RangeType.MED,chipcmd.RangeType.LOW,chipcmd.RangeType.HIGH),
        (chipcmd.RangeType.LOW,chipcmd.RangeType.MED,chipcmd.RangeType.HIGH),
        (chipcmd.RangeType.HIGH,chipcmd.RangeType.HIGH,chipcmd.RangeType.LOW),
        (chipcmd.RangeType.HIGH,chipcmd.RangeType.MED,chipcmd.RangeType.LOW),
        (chipcmd.RangeType.MED,chipcmd.RangeType.HIGH,chipcmd.RangeType.LOW)

    ]
    vga_modes = list(apply_blacklist(itertools.product(*opts_vga),blacklist_vga))
    mul_modes = list(apply_blacklist(itertools.product(*opts_def),blacklist_mult))
    mult.set_scale_modes("mul",mul_modes)
    mult.set_scale_modes("vga",vga_modes)
    for mode in mul_modes:
        in0rng,in1rng,outrng = mode
        scf = outrng.coeff()/(in0rng.coeff()*in1rng.coeff())
        mult.set_info("mul",mode,["in0"],make_ana_props(in0rng,ANALOG_MIN,ANALOG_MAX))
        mult.set_info("mul",mode,["in1"],make_ana_props(in1rng,ANALOG_MIN,ANALOG_MAX))
        mult.set_info("mul",mode,["coeff"],make_dig_props(chipcmd.RangeType.MED, \
                                                          DAC_MIN,DAC_MAX))
        mult.set_info("mul",mode,["out"],make_ana_props(outrng,ANALOG_MIN,ANALOG_MAX))
        mult.set_scale_factor("mul",mode,'out', scf)

    for mode in vga_modes:
        in0rng,outrng = mode
        scf = outrng.coeff()/in0rng.coeff()
        mult.set_info("vga",mode,["in0"],make_ana_props(in0rng,ANALOG_MIN,ANALOG_MAX))
        mult.set_info("vga",mode,["in1"],make_ana_props(chipcmd.RangeType.MED, \
                                                        ANALOG_MIN,ANALOG_MAX))
        mult.set_info("vga",mode,["coeff"],make_dig_props(chipcmd.RangeType.MED,\
                                                          DAC_MIN,DAC_MAX))
        mult.set_info("vga",mode,["out"],make_ana_props(outrng, \
                                                        ANALOG_MIN,ANALOG_MAX))
        mult.set_scale_factor("vga",mode,'out', scf)


'''
.set_prop(["in"],digvar_props) \
.set_prop(["out"], current_props) \
.set_prop(["in"],digvar_props) \
.set_prop(["out"], current_props) \
.set_scale_modes(["pos","neg"]) \
.set_scale_mode("pos") \
.set_scale_factor("out",1.0) \
.set_scale_mode("neg") \
.set_scale_factor("out",-1.0) \
'''
def dac_scale_modes(dac):
    opts = [
        chipcmd.SignType.options(),
        chipcmd.RangeType.options()
    ]
    blacklist = [
        (None,chipcmd.RangeType.LOW)
    ]
    modes = list(apply_blacklist(itertools.product(*opts),blacklist))
    dac.set_scale_modes("*",modes)
    for mode in modes:
        sign,rng = mode
        coeff = sign.coeff()*rng.coeff()*2.0
        dac.set_scale_factor("*",mode,'out', coeff)
        dac.set_info("*",mode,["in"], \
                     make_dig_props(chipcmd.RangeType.MED,DAC_MIN,DAC_MAX))
        dac.set_info("*",mode,["out"],make_ana_props(rng,ANALOG_MIN,ANALOG_MAX))


def fanout_scale_modes(fanout):
    opts = [
        chipcmd.SignType.options(),
        chipcmd.SignType.options(),
        chipcmd.SignType.options(),
        chipcmd.RangeType.options()
    ]
    blacklist = [
        (None,None,None,chipcmd.RangeType.LOW)
    ]
    modes = list(apply_blacklist(itertools.product(*opts),blacklist))
    fanout.set_scale_modes("*",modes)
    for mode in modes:
        inv0,inv1,inv2,rng = mode
        fanout\
            .set_scale_factor("*",mode,"out0",inv0.coeff()) \
            .set_scale_factor("*",mode,"out1",inv1.coeff()) \
            .set_scale_factor("*",mode,"out2",inv2.coeff())
        fanout\
            .set_info("*",mode,["out0","out1","out2","in"],
                      make_ana_props(rng,ANALOG_MIN,ANALOG_MAX))

    fanout.check()


inv_conn = Block('conn_inv',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out","in"], \
          make_ana_props(chipcmd.RangeType.HIGH,\
                         ANALOG_MIN,ANALOG_MAX)) \
.set_scale_factor("*","*","out",-1.0) \
.check()


chip_out = Block('chip_out',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out"], \
          make_ana_props(chipcmd.RangeType.HIGH,\
                         ANALOG_MIN,ANALOG_MAX)) \
.set_info("*","*",["in"], \
          make_ana_props(chipcmd.RangeType.HIGH,\
                         ANALOG_MIN,ANALOG_MAX)) \
.set_scale_factor("*","*","out",1.0) \
.check()

chip_inp = Block('chip_in',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["in"], \
          make_ana_props(chipcmd.RangeType.MED,\
                         ANALOG_MIN,ANALOG_MAX)) \
.set_info("*","*",["out"], \
          make_ana_props(chipcmd.RangeType.MED,\
                         ANALOG_MIN,ANALOG_MAX)) \
.set_scale_factor("*","*","out",1.0) \
.check()


tile_out = Block('tile_out',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out","in"], \
          make_ana_props(chipcmd.RangeType.HIGH,\
                         ANALOG_MIN,ANALOG_MAX)) \
.set_scale_factor("*","*","out",1.0) \
.check()

tile_inp = Block('tile_in',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out","in"], \
          make_ana_props(chipcmd.RangeType.HIGH,\
                         ANALOG_MIN,ANALOG_MAX)) \
.set_scale_factor("*","*","out",1.0) \
.check()

# DUE DAC -> VTOI
ext_chip_in_info = make_dig_props(chipcmd.RangeType.MED,-1.0,1.0,npts=4096)
# do note there's a weird offset of 0..
ext_chip_in_scale_factor = 0.030/0.055*2.0
ext_chip_in = Block('ext_chip_in',type=Block.DAC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.DIGITAL,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["in"],ext_chip_in_info) \
.set_info("*","*",["out"], \
          make_ana_props(chipcmd.RangeType.MED,\
                         ANALOG_MIN,ANALOG_MAX)) \
.set_scale_factor("*","*","out",ext_chip_in_scale_factor) \
.check()


# DUE ADC -> VTOI
ext_chip_out_info = make_dig_props(chipcmd.RangeType.MED,-1.0,1.0,npts=4096)
ext_chip_out_scale_factor = 1.0/2.0
ext_chip_out = Block('ext_chip_out',type=Block.ADC) \
.add_outputs(props.DIGITAL,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out"],ext_chip_out_info) \
.set_info("*","*",["in"], \
          make_ana_props(chipcmd.RangeType.MED,\
                         ANALOG_MIN,ANALOG_MAX)) \
.set_scale_factor("*","*","out",ext_chip_out_scale_factor) \
.check()

tile_dac = Block('tile_dac',type=Block.DAC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.DIGITAL,["in"]) \
.set_op("*","out",ops.Var("in"))
dac_scale_modes(tile_dac)
tile_dac.check()

tile_adc = Block('tile_adc',type=Block.ADC) \
.add_outputs(props.DIGITAL,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out"],None) \
.set_info("*","*",["in"],None) \
.set_scale_factor("*","*","out",1.0) \
.check()

fanout = Block('fanout',type=Block.COPIER) \
.add_outputs(props.CURRENT,["out1","out2","out0"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out0",ops.Var("in")) \
.set_copy("*","out1","out0") \
.set_copy("*","out2","out0")
fanout_scale_modes(fanout)

mult = Block('multiplier') \
.set_comp_modes(["mul","vga"]) \
.add_inputs(props.CURRENT,["in0","in1"]) \
.add_inputs(props.DIGITAL,["coeff"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_op("mul","out",ops.Mult(ops.Var("in0"),ops.Var("in1"))) \
.set_op("vga","out",ops.Mult(ops.Var("coeff"),ops.Var("in0")))
mult_scale_modes(mult)
mult.check()


# TODO: better operating ranges for inputs

integ = Block('integrator') \
.add_inputs(props.CURRENT,["in","ic"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_op("*","out",
        ops.Integ(ops.Var("in"), ops.Var("ic"),
                  handle=':z'
        )
)
integ_scale_modes(integ)
integ.check()

# TODO: better mode-dependent operating ranges
multifun = Block("lut") \
           .set_comp_modes(["ln","exp","sq","sqrt"]) \
           .add_inputs(props.CURRENT,["in"]) \
           .add_outputs(props.CURRENT,["out"])

for mode in ['ln','exp','sq','sqrt']:

    multifun.set_info(mode,"*",["in","out"],  \
                      make_ana_props(chipcmd.RangeType.MED,\
                                     ANALOG_MIN,ANALOG_MAX)) \
            .set_scale_modes(mode,["*"])

multifun.set_op("ln","out",ops.Ln(ops.Var("in"))) \
        .set_op("exp","out",ops.Exp(ops.Var("in"))) \
        .set_op("sq","out",ops.Square(ops.Var("in"))) \
        .set_op("sqrt","out",ops.Sqrt(ops.Var("in"))) \
.check()

def connect(hw,scope1,block1,scope2,block2,negs=[]):
    for loc1 in hw.block_locs(scope1,block1.name):
        for loc2 in hw.block_locs(scope2,block2.name):
            for outport in block1.outputs:
                for inport in block2.inputs:
                    outprop = block1.signals(outport)
                    inprop= block2.signals(inport)
                    if outprop == inprop:
                        hw.conn(block1.name,loc1,outport,
                                block2.name,loc2,inport)

def connect_adj_list(hw,block1,block2,adjlist):
    for loc1,loc2,sign in adjlist:
        do_invert = True if sign == "-" else False
        for outport in block1.outputs:
            for inport in block2.inputs:
                outprop = block1.signals(outport)
                inprop= block2.signals(inport)
                if outprop == inprop:
                    if not do_invert:
                        hw.conn(block1.name,
                                hw.position_string(loc1),
                                outport,
                                block2.name,
                                hw.position_string(loc2),
                                inport)
                    else:
                         hw.conn(block1.name,
                                 hw.position_string(loc1),
                                 outport,
                                 'conn_inv',
                                 hw.position_string(loc1),
                                 'in')
                         hw.conn('conn_inv',
                                 hw.position_string(loc1),
                                 'out',
                                 block2.name,
                                 hw.position_string(loc2),
                                 inport)


def make_board():
    n_chips = 2
    n_tiles = 4
    n_slices = 4
    is_extern_out = lambda tile_no,slice_no : tile_no == 3 \
                    and (slice_no == 2 or slice_no == 3)

    hw = Board("HDACv2",Board.CURRENT_MODE)
    hw.add([multifun,integ,tile_dac,tile_adc,mult,fanout] + \
           [tile_inp,tile_out,chip_inp,chip_out,inv_conn] + \
           [ext_chip_in,ext_chip_out])

    hw.set_time_constant(1.0/TIME_FREQUENCY)

    chips = map(lambda i : hw.layer(i),range(0,n_chips))
    for chip_idx,chip in enumerate(chips):
        tiles = map(lambda i : chip.layer(i), range(0,n_tiles))
        for tile_idx,tile in enumerate(tiles):
            slices = map(lambda i : tile.layer(i),
                         range(0,n_slices))
            for slice_idx,slce in enumerate(slices):
                layer0 = slce.layer(0)
                layer1 = slce.layer(1)
                layer2 = slce.layer(2)
                layer3 = slce.layer(3)

                if slice_idx in [0,2]:
                    layer0.inst('tile_adc')
                    layer0.inst('lut')

                layer0.inst('tile_dac')
                layer0.inst('fanout')
                layer1.inst('fanout')
                layer0.inst('integrator')
                layer0.inst('multiplier')
                layer1.inst('multiplier')


                for layer in [layer0,layer1,layer2,layer3]:
                    layer.inst('tile_in')
                    layer.inst('tile_out')

                if not is_extern_out(tile_idx,slice_idx):
                    slce.inst("chip_out")
                    slce.inst("chip_in")

                else:
                    adc = slce.inst('ext_chip_out')

                    if chip_idx == 0:
                        dac = slce.inst('ext_chip_in')

                    assert(tile_idx == 3)
                    assert(slice_idx == 2 or slice_idx == 3)
                    if slice_idx == 2 and chip_idx == 0:
                        hw.add_handle('A0','ext_chip_out',adc)
                        hw.add_handle('D0','ext_chip_in',dac)
                    elif slice_idx == 3 and chip_idx == 0:
                        hw.add_handle('A1','ext_chip_out',adc)
                        hw.add_handle('D1','ext_chip_in',dac)
                    elif slice_idx == 2 and chip_idx == 1:
                        hw.add_handle('A2','ext_chip_out',adc)
                        #hw.add_handle(dac,handle='D2')
                    elif slice_idx == 3 and chip_idx == 1:
                        hw.add_handle('A3','ext_chip_out',adc)
                        #hw.add_handle(dac,handle='D3')

    chip0_chip1 = [
        ([0,0,0],[1,1,3],'+'),
        ([0,0,1],[1,1,2],'+'),
        ([0,0,2],[1,1,1],'+'),
        ([0,0,3],[1,1,0],'+'),
        ([0,1,0],[1,2,3],'-'),
        ([0,1,1],[1,2,2],'-'),
        ([0,1,2],[1,2,1],'-'),
        ([0,1,3],[1,2,0],'-'),
        ([0,2,0],[1,0,3],'+'),
        ([0,2,1],[1,0,2],'+'),
        ([0,2,2],[1,0,1],'+'),
        ([0,2,3],[1,0,0],'+'),
        ([0,3,0],[1,3,0],'+'),
        ([0,3,1],[1,3,1],'+')
    ]

    chip1_chip0 = [
        ([1,0,0],[0,1,3],'+'),
        ([1,0,1],[0,1,2],'+'),
        ([1,0,2],[0,1,1],'+'),
        ([1,0,3],[0,1,0],'+'),
        ([1,1,0],[0,2,3],'-'),
        ([1,1,1],[0,2,2],'-'),
        ([1,1,2],[0,2,1],'-'),
        ([1,1,3],[0,2,0],'-'),
        ([1,2,0],[0,0,3],'+'),
        ([1,2,1],[0,0,2],'+'),
        ([1,2,2],[0,0,1],'+'),
        ([1,2,3],[0,0,0],'+'),
        ([1,3,0],[0,3,0],'+'),
        ([1,3,1],[0,3,1],'+'),
    ]
    for loc1,loc2,sign in chip0_chip1 + chip1_chip0:
        if sign == "-":
            layer1 = hw.sublayer(loc1)
            layer1.inst('conn_inv')

    hw.freeze_instances()

    for chip1 in range(0,n_chips):
        chip1_layer = hw.layer(chip1)
        for chip2 in range(0,n_chips):
            chip2_layer = hw.layer(chip2)
            if chip1 == chip2:
                continue


            for block1 in [chip_out]:
                for block2 in [chip_inp]:
                    connect_adj_list(hw,block1,block2,chip1_chip0 + chip0_chip1)

    chip1_layer, chip2_layer = None, None
    for chip_no in range(0,n_chips):
        # two of the inputs and outputs on each chip
        # are connected to the board.
        chip_layer = hw.layer(chip_no)
        for tile1 in range(0,n_tiles):
            tile1_layer = chip_layer.layer(tile1)
            for tile2 in range(0,n_tiles):
                tile2_layer = chip_layer.layer(tile2)
                if tile1 == tile2:
                    continue

                for block1 in [tile_out]:
                    for block2 in [tile_inp]:
                        connect(hw,tile1_layer,block1,tile2_layer,block2)

        for tile_no in range(0,n_tiles):
            tile_layer = chip_layer.layer(tile_no)
            for block1 in [mult,integ,fanout,tile_dac,tile_inp]:
                for block2 in [mult,integ,fanout,tile_adc,tile_out]:
                    # FIXME: connect all to all
                    connect(hw,tile_layer,block1,tile_layer,block2)

            for block1 in [tile_out]:
                for block2 in [chip_out,ext_chip_out]:
                    connect(hw,tile_layer,block1,chip_layer,block2)

            for block1 in [chip_inp,ext_chip_in]:
                for block2 in [tile_inp]:
                    connect(hw,chip_layer,block1,tile_layer,block2)


            for block1 in [tile_adc]:
                for block2 in [multifun]:
                    #FIXME: connect all to all
                    connect(hw,tile_layer,block1,tile_layer,block2)


            for block1 in [multifun]:
                for block2 in [tile_dac]:
                    #FIXME: connect all to all
                    connect(hw,tile_layer,block1,tile_layer,block2)

    return hw

board = make_board()
