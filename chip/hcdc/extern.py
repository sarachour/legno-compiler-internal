from chip.block import Block, BlockType
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chip_command as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops


# DUE DAC -> VTOI
ext_chip_in_props = util.make_dig_props(chipcmd.RangeType.MED,-1.0,1.0,npts=4096)
# do note there's a weird offset of 0..
ext_chip_in_coeff = 0.030/0.055*2.0
block_in = Block('ext_chip_in',type=BlockType.DAC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.DIGITAL,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["in"],ext_chip_in_props) \
.set_props("*","*",["out"], \
          util.make_ana_props(chipcmd.RangeType.MED,\
                              glb.ANALOG_MIN,
                              glb.ANALOG_MAX)) \
.set_coeff("*","*","out",ext_chip_in_coeff) \
.check()


# DUE ADC -> VTOI
ext_chip_out_props = util.make_dig_props(chipcmd.RangeType.MED,-1.0,1.0,npts=4096)
ext_chip_out_coeff = 1.0/2.0
block_out = Block('ext_chip_out',type=BlockType.ADC) \
.add_outputs(props.DIGITAL,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["out"],ext_chip_out_props) \
.set_props("*","*",["in"], \
          util.make_ana_props(chipcmd.RangeType.MED,\
                              glb.ANALOG_MIN,
                              glb.ANALOG_MAX)) \
.set_coeff("*","*","out",ext_chip_out_coeff) \
.check()
