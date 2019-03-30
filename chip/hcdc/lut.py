from chip.block import Block
import chip.props as props
import chip.units as units
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import chip.cont as cont
import ops.op as ops

def lut_continuous_model(xbar):
  csm = cont.ContinuousScaleModel()
  csm.set_baseline("*")
  out = csm.decl_var(cont.CSMOpVar("out"))
  inp = csm.decl_var(cont.CSMOpVar("in"))
  coeff = csm.decl_var(cont.CSMCoeffVar("out"))
  csm.eq(ops.Mult(ops.Var(inp.varname),
                  ops.Var(coeff.varname)), \
         ops.Var(out.varname))
  csm.discrete.add_mode("*")
  xbar.set_scale_model("*", csm)
  csm.discrete.add_cstr("*",inp,1.0)
  csm.discrete.add_cstr("*",out,1.0)

block = Block("lut") \
           .add_inputs(props.DIGITAL,["in"]) \
           .add_outputs(props.DIGITAL,["out"])


digital_props = util.make_dig_props(chipcmd.RangeType.MED,\
                                    glb.DAC_MIN, glb.DAC_MAX,
                                    glb.ANALOG_DAC_SAMPLES)

digital_props.set_continuous(0,glb.MAX_FREQ_LUT,units.khz)
block.set_scale_modes("*",["*"])
block.set_props("*","*",["in","out"],  digital_props)

block.set_op("*","out",ops.Func(["in"],None)) \
.check()
lut_continuous_model(block)
