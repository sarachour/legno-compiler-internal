from chip.block import Block
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chip_command as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops

block = Block("lut") \
           .set_comp_modes(["ln","exp","sq","sqrt"]) \
           .add_inputs(props.CURRENT,["in"]) \
           .add_outputs(props.CURRENT,["out"])

for mode in ['ln','exp','sq','sqrt']:

    block.set_props(mode,"*",["in","out"],  \
                      util.make_ana_props(chipcmd.RangeType.MED,\
                                          glb.ANALOG_MIN,
                                          glb.ANALOG_MAX)) \
            .set_scale_modes(mode,["*"])

block.set_op("ln","out",ops.Ln(ops.Var("in"))) \
     .set_op("exp","out",ops.Exp(ops.Var("in"))) \
     .set_op("sq","out",ops.Square(ops.Var("in"))) \
     .set_op("sqrt","out",ops.Sqrt(ops.Var("in"))) \
.check()
