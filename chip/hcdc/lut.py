from chip.block import Block
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chip_command as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops

block = Block("lut") \
           .add_inputs(props.DIGITAL,["in"]) \
           .add_outputs(props.DIGITAL,["out"])

mode = "*"
block.set_props(mode,"*",["in","out"],  \
                util.make_dig_props(chipcmd.RangeType.MED,\
                                    glb.DAC_MIN,
                                    glb.DAC_MAX)) \
     .set_scale_modes(mode,["*"])

block.set_op(mode,"out",ops.Func(["in"],None)) \
.check()
