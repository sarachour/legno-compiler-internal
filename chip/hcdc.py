import props
import units
import ops.op as ops
from chip.block import Block
from chip.board import Board

current_props = props.AnalogProperties() \
.set_interval(-1.0,1.0,unit=units.uA)

current_integ_props = props.AnalogProperties() \
.set_interval(-1.2,1.2,unit=units.uA)


hcdcv2_values = list(map(lambda x :x/256.0*2.0-1.0, range(0,256)))
digval_props = props.DigitalProperties() \
.set_values(hcdcv2_values) \
.set_constant() \
.check()

digvar_props = props.DigitalProperties() \
.set_values(hcdcv2_values) \
.set_continuous() \
.check()


#TODO: proper conversion rate.
due_dac_props = props.DigitalProperties() \
.set_values(hcdcv2_values) \
.set_sample(3,unit=units.us) \
.check()


due_adc_props = props.DigitalProperties() \
.set_values(hcdcv2_values) \
.set_sample(3,unit=units.us) \
.check()


inv_conn = Block('conn_inv',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("out",ops.Var("in")) \
.set_prop(["out","in"], current_props) \
.set_scale_modes(["inv"]) \
.set_scale_mode("inv") \
.set_scale_factor("out",-1.0) \
.check()


chip_out = Block('chip_out',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("out",ops.Var("in")) \
.set_prop(["out","in"], current_props) \
.check()

chip_inp = Block('chip_in',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("out",ops.Var("in")) \
.set_prop(["out","in"], current_props) \
.check()


tile_out = Block('tile_out',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("out",ops.Var("in")) \
.set_prop(["out","in"], current_props) \
.check()

tile_inp = Block('tile_in',type=Block.BUS) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("out",ops.Var("in")) \
.set_prop(["out","in"], current_props) \
.check()


due_dac = Block('due_dac',type=Block.DAC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.DIGITAL,["in"]) \
.set_op("out",ops.Var("in")) \
.set_prop(["in"],due_dac_props) \
.set_prop(["out"], current_props) \
.set_external() \
.check()


due_adc = Block('due_adc',type=Block.ADC) \
.add_outputs(props.DIGITAL,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("out",ops.Var("in")) \
.set_prop(["out"],due_adc_props) \
.set_prop(["in"],current_props) \
.set_external() \
.check()



tile_dac = Block('tile_dac',type=Block.DAC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.DIGITAL,["in"]) \
.set_prop(["in"],digvar_props) \
.set_prop(["out"], current_props) \
.set_op("out",ops.Var("in")) \
.set_prop(["in"],digvar_props) \
.set_prop(["out"], current_props) \
.set_scale_modes(["pos","neg"]) \
.set_scale_mode("pos") \
.set_scale_factor("out",1.0) \
.set_scale_mode("neg") \
.set_scale_factor("out",-1.0) \
.check()


tile_adc = Block('tile_adc',type=Block.ADC) \
.add_outputs(props.DIGITAL,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("out",ops.Var("in")) \
.set_prop(["out"],digvar_props) \
.set_prop(["in"],current_props) \
.check()

fanout = Block('fanout',type=Block.COPIER) \
.add_outputs(props.CURRENT,["out1","out2","out0"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("out0",ops.Var("in")) \
.set_copy("out1","out0") \
.set_copy("out2","out0") \
.set_prop(["out0","out1","out2","in"],current_props)

modes = []
for inv0 in ["pos","neg"]:
    for inv1 in ["pos","neg"]:
        for inv2 in ["pos","neg"]:
            modes.append([inv0,inv1,inv2])


fanout.set_scale_modes(modes)
for inv0,inv1,inv2 in modes:
    fanout\
        .set_scale_mode([inv0,inv1,inv2])\
        .set_scale_factor("out0",1.0 if inv0 else -1.0) \
        .set_scale_factor("out1",1.0 if inv1 else -1.0) \
        .set_scale_factor("out2",1.0 if inv2 else -1.0)

fanout.check()


tcs = {
    #'hi': 0.1,
    'med': 1,
    #'low': 10
}
mult_scf = 1.0
#mult_scf = 1.0
mult = Block('multiplier') \
.set_modes(["default","vga"]) \
.add_inputs(props.CURRENT,["in0","in1"]) \
.add_inputs(props.DIGITAL,["coeff"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_mode("default") \
.set_prop(["coeff"],digval_props) \
.set_prop(["in0","in1","out"],current_props) \
.set_op("out",ops.Mult(ops.Var("in0"),ops.Var("in1"))) \
.set_mode("vga") \
.set_prop(["coeff"],digval_props) \
.set_prop(["in0","in1","out"],current_props) \
.set_op("out",ops.Mult(ops.Var("coeff"),ops.Var("in0"))) \

modes = []
for scf in tcs.keys():
    modes.append(scf)

mult.set_scale_modes(modes)

for scf in modes:
    mult.set_scale_mode(scf) \
        .set_scale_factor("out",tcs[scf])

mult.check()


# TODO: better operating ranges for inputs

integ = Block('integrator') \
.add_inputs(props.CURRENT,["in"]) \
.add_inputs(props.CURRENT,["ic"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_op("out",
        ops.Integ(ops.Var("in"), ops.Var("ic")),
        integrate=True
) \
.set_prop(["in","out"], current_integ_props) \
.set_prop(["ic"], digval_props)

modes = []
for speed_out in tcs.keys():
    for speed_in in tcs.keys():
        for direction in ["pos","neg"]:
            modes.append([speed_out,speed_in,direction])

integ.set_scale_modes(modes)

for mode in modes:
    flip_it = 1.0 if mode[2] == "pos" else -1.0
    integ \
    .set_scale_mode(mode) \
    .set_scale_factor("out",tcs[mode[0]]*flip_it) \
    .set_scale_factor("in",tcs[mode[1]])

integ.check()

# TODO: better mode-dependent operating ranges
multifun = Block("lut") \
.add_inputs(props.CURRENT,["in"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_modes(["ln","exp","sq","sqrt"]) \
.set_mode("ln") \
.set_op("out",ops.Ln(ops.Var("in"))) \
.set_prop(["in","out"], current_props) \
.set_mode("exp") \
.set_op("out",ops.Exp(ops.Var("in"))) \
.set_prop(["in","out"], current_props) \
.set_mode("sq") \
.set_op("out",ops.Square(ops.Var("in"))) \
.set_prop(["in","out"], current_props) \
.set_mode("sqrt") \
.set_op("out",ops.Sqrt(ops.Var("in"))) \
.set_prop(["in","out"], current_props) \
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
                        hw.conn(block1.name,loc1,outport,
                                block2.name,loc2,inport)
                    else:
                         hw.conn(block1.name,loc1,outport,
                                 'conn_inv',loc1,'in')
                         hw.conn('conn_inv',loc1,'out',
                                 block2.name,loc2,inport)


def make_board():
    n_chips = 2
    n_tiles = 4
    n_slices = 4
    is_extern_out = lambda tile_no,slice_no : tile_no == 3 \
                    and (slice_no == 2 or slice_no == 3)

    hw = Board("HDACv2",Board.CURRENT_MODE)
    hw.add([multifun,integ,tile_dac,tile_adc,mult,fanout] + \
           [tile_inp,tile_out,chip_inp,chip_out,inv_conn] + \
           [due_dac,due_adc])


    hw.set_meta("hardware_time_us", 126000)
    hw.set_meta("adc_sample_us", 3)
    hw.set_meta("adc_delta", 1.0/128)

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
                    slce.inst('due_dac')
                    adc = slce.inst('due_adc')
                    assert(tile_idx == 3)
                    assert(slice_idx == 2 or slice_idx == 3)

                    chip_base = 4 if chip_idx == 1 else 0
                    slice_base = 2 if slice_idx == 2 else 0

                    hw.set_inst_meta('due_adc',
                                slce.position,
                                "chan_pos",
                                chip_base+slice_base+0)

                    hw.set_inst_meta('due_adc',
                                slce.position,
                                "chan_neg",
                                chip_base+slice_base+1)



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
                for block2 in [chip_out,due_adc]:
                    connect(hw,tile_layer,block1,chip_layer,block2)

            for block1 in [chip_inp,due_dac]:
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
