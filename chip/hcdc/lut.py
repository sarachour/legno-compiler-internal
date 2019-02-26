from chip.block import Block
import chip.props as props
import chip.units as units
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops

block = Block("lut") \
           .add_inputs(props.DIGITAL,["in"]) \
           .add_outputs(props.DIGITAL,["out"])


digital_props = util.make_dig_props(chipcmd.RangeType.MED,\
                                    glb.DAC_MIN, glb.DAC_MAX,
                                    glb.MAX_DAC_ERROR_DYNAMIC,
                                    glb.ANALOG_DAC_SAMPLES)

digital_props.set_continuous(0,glb.MAX_FREQ_LUT,units.khz)
block.set_scale_modes("*",["*"])
block.set_props("*","*",["in","out"],  digital_props)

block.set_op("*","out",ops.Func(["in"],None)) \
.check()
