from chip.block import Block, BlockType
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import chip.units as units
from chip.cont import *


def extern_continuous_model(xbar):
  csm = ContinuousScaleModel()
  csm.set_baseline("*")
  out = csm.decl_var(CSMOpVar("out"))
  inp = csm.decl_var(CSMOpVar("in"))
  coeff = csm.decl_var(CSMCoeffVar("out"))
  csm.eq(ops.Mult(ops.Var(inp.varname),
                  ops.Var(coeff.varname)), \
         ops.Var(out.varname))
  inp.set_interval(1.0,1.0)
  coeff.set_interval(1.0,1.0)
  out.set_interval(1.0,1.0)
  csm.add_scale_mode("*",[])
  xbar.set_scale_model("*", csm)


# DUE DAC -> VTOI
ext_chip_in_props = util.make_dig_props(chipcmd.RangeType.MED, \
                                        -1.0,1.0,
                                        glb.EXT_DAC_SAMPLES)
ext_chip_in_props.set_min_quantize(ext_chip_in_props.SignalType.DYNAMIC, \
                                   glb.MIN_QUANT_EXTIN_DYNAMIC)
ext_chip_in_props.set_clocked(10,500,units.us)
# do note there's a weird offset of 0..
#ext_chip_in_coeff = 0.030/0.055*2.0
ext_chip_in_coeff = 1.0
block_in = Block('ext_chip_in',type=BlockType.DAC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.DIGITAL,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["in"],ext_chip_in_props) \
.set_props("*","*",["out"], \
          util.make_ana_props(chipcmd.RangeType.MED,\
                              glb.ANALOG_MIN,
                              glb.ANALOG_MAX,
                              glb.ANALOG_MINSIG_CONST,
                              glb.ANALOG_MINSIG_DYN)) \
.set_coeff("*","*","out",ext_chip_in_coeff) \
.check()
extern_continuous_model(block_in)


# DUE ADC -> VTOI
ext_chip_out_props = util.make_dig_props(chipcmd.RangeType.MED, \
                                         -2.0,2.0, \
                                         glb.EXT_DAC_SAMPLES)
ext_chip_out_props.set_min_quantize(ext_chip_in_props.SignalType.DYNAMIC, \
                                   glb.MIN_QUANT_EXTOUT_DYNAMIC)

#sample rate
ext_chip_out_props.set_clocked(1,None,units.ns)
# for adc
#ext_chip_out_props.set_clocked(1,units.ns)
ext_chip_out_coeff = 1.0
block_out = Block('ext_chip_out',type=BlockType.ADC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["out"],ext_chip_out_props) \
.set_props("*","*",["in"], \
          util.make_ana_props(chipcmd.RangeType.MED,\
                              glb.ANALOG_MIN,
                              glb.ANALOG_MAX,
                              glb.ANALOG_MINSIG_CONST,
                              glb.ANALOG_MINSIG_DYN)) \
.set_coeff("*","*","out",ext_chip_out_coeff) \
.check()
extern_continuous_model(block_out)
