from hwlib.block import Block
import hwlib.props as props
import hwlib.units as units
import hwlib.hcdc.util as util
import hwlib.hcdc.globals as glb
import hwlib.hcdc.enums as enums
import ops.op as ops

block = Block("lut") \
           .add_inputs(props.DIGITAL,["in"]) \
           .add_outputs(props.DIGITAL,["out"]) \
           .set_comp_modes(["*"], \
                           glb.HCDCSubset.all_subsets()) \
           .set_scale_modes("*",["*"], \
                            glb.HCDCSubset.all_subsets()) \



digital_props = util.make_dig_props(enums.RangeType.MED,\
                                    glb.CTX.get(glb.GLProp.DIGITAL_INTERVAL,
                                            "lut","*","*",None),
                                    glb.CTX.get(glb.GLProp.DIGITAL_QUANTIZE,
                                            "lut","*","*",None)
)

digital_props.set_continuous(0,glb.CTX.get(glb.GLProp.MAX_FREQ, \
                                       "lut","*","*",None))

block.set_props("*","*",["in","out"],  digital_props)

block.set_op("*","out",ops.Func(["in"],None)) \
.check()
