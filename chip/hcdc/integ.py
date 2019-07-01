from chip.block import Block
import chip.props as props
import chip.units as units
import chip.hcdc.util as util
import util.util as gutil
import chip.cont as cont

import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
from chip.hcdc.globals import CTX, GLProp
import ops.op as ops
import chip.cont as contlib
import itertools

def get_comp_modes():
  return chipcmd.SignType.options()

def get_scale_modes():
  opts = [
    chipcmd.RangeType.options(),
    chipcmd.RangeType.options()
  ]
  blacklist = [
    (chipcmd.RangeType.LOW,chipcmd.RangeType.HIGH),
    (chipcmd.RangeType.HIGH,chipcmd.RangeType.LOW)
  ]
  modes = list(util.apply_blacklist(itertools.product(*opts),\
                                    blacklist))
  return modes

def is_extended(scale_mode):
  i,o = scale_mode
  #return i == chipcmd.RangeType.MED and \
  #  (o == chipcmd.RangeType.MED or \
  #   o == chipcmd.RangeType.LOW)
  return (i == chipcmd.RangeType.MED or \
          i == chipcmd.RangeType.HIGH) and \
          o == chipcmd.RangeType.MED

def is_standard(scale_mode):
  i,o = scale_mode
  return i == chipcmd.RangeType.MED and \
    o == chipcmd.RangeType.MED

def continuous_scale_model(integ):
  m = chipcmd.RangeType.MED
  comp_modes = get_comp_modes()
  scale_modes = get_scale_modes()
  for comp_mode in comp_modes:
    csm = cont.ContinuousScaleModel()
    csm.set_baseline((m,m))
    integ.set_scale_model(comp_mode,csm)

def scale_model(integ):
  comp_modes = get_comp_modes()
  scale_modes = list(get_scale_modes())
  for comp_mode in comp_modes:
    standard,nonstandard = gutil.partition(is_standard,scale_modes)
    extended,_ = gutil.partition(is_extended,scale_modes)
    integ.set_scale_modes(comp_mode,standard,glb.HCDCSubset.all_subsets())
    integ.set_scale_modes(comp_mode,nonstandard,[glb.HCDCSubset.UNRESTRICTED])
    integ.add_subsets(comp_mode,extended,[glb.HCDCSubset.EXTENDED])
    for scale_mode in scale_modes:
      get_prop = lambda p : CTX.get(p, integ.name,
                                    comp_mode,scale_mode,None)
      inrng,outrng = scale_mode
      analog_in = util.make_ana_props(inrng, \
                                      get_prop(GLProp.CURRENT_INTERVAL))
      analog_in.set_bandwidth(0,get_prop(GLProp.MAX_FREQ),units.hz)

      analog_out = util.make_ana_props(outrng, \
                                       get_prop(GLProp.CURRENT_INTERVAL))
      dig_props = util.make_dig_props(chipcmd.RangeType.MED,
                                      get_prop(GLProp.DIGITAL_INTERVAL), \
                                      get_prop(GLProp.DIGITAL_QUANTIZE))
      dig_props.set_exclude(get_prop(GLProp.DIGITAL_EXCLUDE))
      dig_props.set_constant()
      integ.set_props(comp_mode,scale_mode,['in'],analog_in)
      integ.set_props(comp_mode,scale_mode,["ic"], dig_props)
      integ.set_props(comp_mode,scale_mode,["out"],\
                      analog_out,
                      handle=":z[0]")
      integ.set_props(comp_mode,scale_mode,["out"],\
                      analog_out,
                      handle=":z")
      integ.set_props(comp_mode,scale_mode,["out"],
                      analog_out,
                      handle=":z'")
      integ.set_props(comp_mode,scale_mode,["out"],
                      analog_out)

      scf_inout = outrng.coeff()/inrng.coeff()
      # alteration: initial condition, is not scaled
      scf_ic = outrng.coeff()*2.0
      integ.set_coeff(comp_mode,scale_mode,"out",scf_inout,handle=':z\'')
      integ.set_coeff(comp_mode,scale_mode,"out",scf_ic,':z[0]')
      integ.set_coeff(comp_mode,scale_mode,"out",1.0,handle=':z')
      integ.set_coeff(comp_mode,scale_mode,"out",1.0)

block = Block('integrator',) \
.set_comp_modes(get_comp_modes(),glb.HCDCSubset.all_subsets()) \
.add_inputs(props.CURRENT,["in","ic"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_op(chipcmd.SignType.POS,"out",
        ops.Integ(ops.Var("in"), ops.Var("ic"),
                  handle=':z'
        )
) \
.set_op(chipcmd.SignType.NEG,"out",
        ops.Integ(ops.Mult(ops.Const(-1),ops.Var("in")), \
        ops.Var("ic"),
        handle=':z')
)
scale_model(block)
continuous_scale_model(block)
block.check()

