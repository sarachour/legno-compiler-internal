from chip.block import Block
import chip.props as props
import chip.units as units
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import chip.cont as cont
import ops.op as ops
from chip.hcdc.globals import CTX, GLProp

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
           .add_outputs(props.DIGITAL,["out"]) \
           .set_comp_modes(["*"], \
                           glb.HCDCSubset.all_subsets()) \
           .set_scale_modes("*",["*"], \
                            glb.HCDCSubset.all_subsets()) \



digital_props = util.make_dig_props(chipcmd.RangeType.MED,\
                                    CTX.get(GLProp.DIGITAL_INTERVAL,
                                            "lut","*","*",None),
                                    CTX.get(GLProp.DIGITAL_QUANTIZE,
                                            "lut","*","*",None)
)

digital_props.set_continuous(0,CTX.get(GLProp.MAX_FREQ, \
                                       "lut","*","*",None))

block.set_props("*","*",["in","out"],  digital_props)

block.set_op("*","out",ops.Func(["in"],None)) \
.check()
lut_continuous_model(block)
