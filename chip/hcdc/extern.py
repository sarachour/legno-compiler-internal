from chip.block import Block, BlockType
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import chip.units as units
from chip.cont import *
from chip.hcdc.globals import CTX, GLProp


def extern_analog_in_cont_model(xbar):
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
props_in = util.make_ana_props(chipcmd.RangeType.HIGH,\
                                CTX.get(GLProp.VOLTAGE_INTERVAL,
                                        'ext_chip_analog_in', \
                                        "*","*",'in'))
props_in.set_physical(True)

props_out = util.make_ana_props(chipcmd.RangeType.HIGH,\
                                CTX.get(GLProp.CURRENT_INTERVAL,
                                        'ext_chip_analog_in', \
                                        "*","*",'out'))
coeff = CTX.get(GLProp.COEFF,"ext_chip_analog_in",
                    "*","*","out")

block_analog_in = Block('ext_chip_analog_in') \
                  .set_comp_modes(["*"], \
                                  glb.HCDCSubset.all_subsets()) \
                  .set_scale_modes("*",["*"], \
                                   glb.HCDCSubset.all_subsets()) \
                  .add_outputs(props.CURRENT,["out"]) \
                  .add_inputs(props.CURRENT,["in"]) \
                  .set_op("*","out",ops.Var("in")) \
                  .set_props("*","*",["in"],props_in) \
                  .set_props("*","*",["out"], props_out) \
                  .set_coeff("*","*","out",coeff) \
                  .check()
extern_analog_in_cont_model(block_analog_in)


def extern_in_cont_model(xbar):
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

coeff = CTX.get(GLProp.COEFF,"ext_chip_in",
                    "*","*","out")

props_in = util.make_dig_props(chipcmd.RangeType.MED, \
                               CTX.get( GLProp.DIGITAL_INTERVAL, \
                                        'ext_chip_in', \
                                        "*","*",'in'), \
                               CTX.get(GLProp.DIGITAL_QUANTIZE, \
                                       'ext_chip_in', \
                                       "*","*","in"))

# sample rate is 10 us
props_in.set_clocked(CTX.get(GLProp.DIGITAL_SAMPLE, \
                             "ext_chip_in",
                             "*","*",None),
                     CTX.get(GLProp.INBUF_SIZE,
                             'ext_chip_in',
                             "*","*",None))

props_out = util.make_ana_props(chipcmd.RangeType.HIGH,\
                                CTX.get(GLProp.CURRENT_INTERVAL,
                                        'ext_chip_in', \
                                        "*","*",'out'))
block_in = Block('ext_chip_in',type=BlockType.DAC) \
                                     .set_comp_modes(["*"], \
                                                     glb.HCDCSubset.all_subsets()) \
                                     .set_scale_modes("*",["*"], \
                                                      glb.HCDCSubset.all_subsets()) \
                                     .add_outputs(props.CURRENT,["out"]) \
                                     .add_inputs(props.DIGITAL,["in"]) \
                                     .set_op("*","out",ops.Var("in")) \
                                     .set_props("*","*",["in"],props_in) \
                                     .set_props("*","*",["out"], props_out) \
                                     .set_coeff("*","*","out",coeff) \
                                     .check()
extern_in_cont_model(block_in)

def extern_out_cont_model(xbar):
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


coeff = CTX.get(GLProp.COEFF,"ext_chip_out",
                    "*","*","out")

# DUE ADC -> VTOI
props_out = util.make_dig_props(chipcmd.RangeType.MED, \
                                         CTX.get(GLProp.DIGITAL_INTERVAL,
                                                 'ext_chip_out',
                                                 "*","*","out"),
                                         CTX.get(GLProp.DIGITAL_QUANTIZE,
                                                 "ext_chip_out",
                                                 "*","*",None))

#sample rate is 1 ns
props_out.set_clocked(CTX.get(GLProp.DIGITAL_SAMPLE, \
                              "ext_chip_out",
                              "*","*",None),
                     CTX.get(GLProp.OUTBUF_SIZE,
                             'ext_chip_out',
                             "*","*",None))

# for adc
#ext_chip_out_props.set_clocked(1,units.ns)
props_in = util.make_ana_props(chipcmd.RangeType.MED,\
                                CTX.get(GLProp.CURRENT_INTERVAL,
                                        'ext_chip_out', \
                                        "*","*",'in'))
block_out = Block('ext_chip_out',type=BlockType.ADC) \
                                       .set_comp_modes(["*"], \
                                                       glb.HCDCSubset.all_subsets()) \
                                       .set_scale_modes("*",["*"], \
                                                        glb.HCDCSubset.all_subsets()) \
                                       .add_outputs(props.CURRENT,["out"]) \
                                       .add_inputs(props.CURRENT,["in"]) \
                                       .set_op("*","out",ops.Var("in")) \
                                       .set_props("*","*",["out"],props_out) \
                                       .set_props("*","*",["in"], props_in) \
                                       .set_coeff("*","*","out",coeff) \
                                       .check()
extern_out_cont_model(block_out)
