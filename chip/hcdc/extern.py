from chip.block import Block, BlockType
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import chip.units as units
from chip.cont import *


def extern_continuous_in_model(xbar):
  csm = ContinuousScaleModel()
  csm.set_baseline("*")
  out = csm.decl_var(CSMOpVar("out"))
  inp = csm.decl_var(CSMOpVar("in"))
  coeff = csm.decl_var(CSMCoeffVar("out"))
  csm.eq(ops.Mult(ops.Var(inp.varname),
                  ops.Var(coeff.varname)), \
         ops.Var(out.varname))
  csm.discrete.add_mode("*")
  csm.discrete.add_cstr("*",out,1.0)
  csm.discrete.add_cstr("*",inp,1.0)
  xbar.set_scale_model("*", csm)


# DUE DAC -> VTOI
ext_chip_in_coeff = 2.0
ext_chip_in_props = util.make_dig_props(chipcmd.RangeType.MED, \
                                        glb.ANALOG_MIN/ext_chip_in_coeff,
                                        glb.ANALOG_MAX/ext_chip_in_coeff,
                                        glb.EXT_DAC_SAMPLES)
ext_chip_in_props.set_clocked(10,glb.MAX_BUFFER_DAC_SAMPLES,units.us)

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
extern_continuous_in_model(block_in)

def extern_continuous_out_model(xbar):
  csm = ContinuousScaleModel()
  csm.set_baseline("*")
  out = csm.decl_var(CSMOpVar("out"))
  inp = csm.decl_var(CSMOpVar("in"))
  coeff = csm.decl_var(CSMCoeffVar("out"))
  csm.eq(ops.Mult(ops.Var(inp.varname),
                  ops.Var(coeff.varname)), \
         ops.Var(out.varname))

  csm.discrete.add_mode("*")
  csm.discrete.add_cstr("*",inp,1.0)
  csm.discrete.add_cstr("*",out,1.0)
  xbar.set_scale_model("*", csm)



# DUE ADC -> VTOI
ext_chip_out_coeff = 2.7/2.0
ext_chip_out_props = util.make_dig_props(chipcmd.RangeType.MED, \
                                         glb.ANALOG_MIN*ext_chip_out_coeff,
                                         glb.ANALOG_MAX*ext_chip_out_coeff, \
                                         glb.EXT_DAC_SAMPLES)

#sample rate
ext_chip_out_props.set_clocked(1,glb.MAX_BUFFER_ADC_SAMPLES,units.ns)
# for adc
#ext_chip_out_props.set_clocked(1,units.ns)
block_out = Block('ext_chip_out',type=BlockType.ADC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["out"],ext_chip_out_props) \
.set_props("*","*",["in"], \
          util.make_ana_props(chipcmd.RangeType.MED,\
                              glb.ANALOG_MIN,
                              glb.ANALOG_MAX)) \
.set_coeff("*","*","out",ext_chip_out_coeff) \
.check()
extern_continuous_out_model(block_out)
