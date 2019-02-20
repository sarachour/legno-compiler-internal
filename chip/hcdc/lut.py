from chip.block import Block
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops

block = Block("lut") \
           .add_inputs(props.DIGITAL,["in"]) \
           .add_outputs(props.DIGITAL,["out"])


block.set_scale_modes("*",["*"])
block.set_props("*","*",["in","out"],  \
                util.make_dig_props(chipcmd.RangeType.MED,\
                                    glb.DAC_MIN,
                                    glb.DAC_MAX)) \

block.set_op("*","out",ops.Func(["in"],None)) \
.check()
