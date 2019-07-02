from chip.block import Block
import chip.props as props
import chip.hcdc.util as util
import chip.units as units
from chip.cont import *
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import ops.nop as nops
import itertools
from chip.hcdc.globals import CTX, GLProp

# 10.0 >= coeff >= 0.1
# 10.0 >= in0 >= 0.1
# 10.0 >= in1 >= 0.1
# 10.0 >= out >= 0.1
# out = in0*in1*coeff

def get_modes():
  opts_def = [
    chipcmd.RangeType.options(),
    chipcmd.RangeType.options(),
    chipcmd.RangeType.options()
  ]

  opts_vga = [
    chipcmd.RangeType.options(),
    chipcmd.RangeType.options()
  ]
  blacklist_vga = [
    (chipcmd.RangeType.LOW,chipcmd.RangeType.HIGH)
  ]
  blacklist_mult = [
    (chipcmd.RangeType.LOW,chipcmd.RangeType.LOW, \
     chipcmd.RangeType.HIGH),
    (chipcmd.RangeType.MED,chipcmd.RangeType.LOW, \
     chipcmd.RangeType.HIGH),
    (chipcmd.RangeType.LOW,chipcmd.RangeType.MED, \
     chipcmd.RangeType.HIGH),
    (chipcmd.RangeType.HIGH,chipcmd.RangeType.HIGH, \
     chipcmd.RangeType.LOW),
    (chipcmd.RangeType.HIGH,chipcmd.RangeType.MED, \
     chipcmd.RangeType.LOW),
    (chipcmd.RangeType.MED,chipcmd.RangeType.HIGH, \
     chipcmd.RangeType.LOW)

  ]
  vga_modes = list(util.apply_blacklist(itertools.product(*opts_vga),
                                   blacklist_vga))
  mul_modes = list(util.apply_blacklist(itertools.product(*opts_def),
                                   blacklist_mult))
  return vga_modes,mul_modes

def is_standard_vga(mode):
  i,o = mode
  return i == chipcmd.RangeType.MED and \
    o == chipcmd.RangeType.MED


def is_extended_vga(mode):
  i,o = mode
  #return (i == chipcmd.RangeType.LOW or \
  return (i == chipcmd.RangeType.MED or \
          i == chipcmd.RangeType.MED) and \
          (o == chipcmd.RangeType.MED)
# it works with high.

def is_extended2_vga(mode):
  i,o = mode
  #return (i == chipcmd.RangeType.LOW or \
  return (i == chipcmd.RangeType.MED or \
          i == chipcmd.RangeType.MED) and \
          (o == chipcmd.RangeType.MED)
# it works with high.


def is_standard_mul(mode):
  i0,i1,o = mode
  return i0 == chipcmd.RangeType.MED and \
    i1 == chipcmd.RangeType.MED and \
    o == chipcmd.RangeType.MED


def is_extended_mul(mode):
  i0,i1,o = mode
  return i0 == chipcmd.RangeType.MED and \
    i1 == chipcmd.RangeType.MED and \
    o == chipcmd.RangeType.MED


def is_extended2_mul(mode):
  i0,i1,o = mode
  return i0 == chipcmd.RangeType.MED and \
    i1 == chipcmd.RangeType.MED and \
    o == chipcmd.RangeType.MED


def continuous_scale_model_vga(mult):
  vga_modes,_= get_modes()
  m = chipcmd.RangeType.MED

  csm = ContinuousScaleModel()
  csm.set_baseline((m,m))

  mult.set_scale_model('vga',csm)

def continuous_scale_model_mult(mult):
  _,mul_modes = get_modes()
  m = chipcmd.RangeType.MED

  csm = ContinuousScaleModel()
  csm.set_baseline((m,m,m))
  mult.set_scale_model('mul',csm)

def continuous_scale_model(mult):
  continuous_scale_model_vga(mult)
  continuous_scale_model_mult(mult)


def scale_model(mult):
  vga_modes,mul_modes = get_modes()
  std,nonstd = gutil.partition(is_standard_mul,mul_modes)
  ext,_ = gutil.partition(is_extended_mul,mul_modes)
  ext2,_ = gutil.partition(is_extended2_mul,mul_modes)
  mult.set_scale_modes("mul",std,glb.HCDCSubset.all_subsets())
  mult.set_scale_modes("mul",nonstd,[glb.HCDCSubset.UNRESTRICTED])
  mult.add_subsets("mul",ext,[glb.HCDCSubset.EXTENDED])

  std,nonstd = gutil.partition(is_standard_vga,vga_modes)
  ext,_ = gutil.partition(is_extended_vga,vga_modes)
  ext2,_ = gutil.partition(is_extended2_vga,vga_modes)
  mult.set_scale_modes("vga",std,glb.HCDCSubset.all_subsets())
  mult.set_scale_modes("vga",nonstd,[glb.HCDCSubset.UNRESTRICTED])
  mult.add_subsets("vga",ext,[glb.HCDCSubset.EXTENDED])

  for mode in mul_modes:
      in0rng,in1rng,outrng = mode
      get_prop = lambda p : CTX.get(p, mult.name,
                                    'mul',mode,None)
      # ERRATA: virtual scale of 0.5
      scf = 0.5*outrng.coeff()/(in0rng.coeff()*in1rng.coeff())
      dig_props = util.make_dig_props(chipcmd.RangeType.MED, \
                                      get_prop(GLProp.DIGITAL_INTERVAL),
                                      get_prop(GLProp.DIGITAL_QUANTIZE))
      dig_props.set_exclude(get_prop(GLProp.DIGITAL_EXCLUDE));
      dig_props.set_constant()
      mult.set_props("mul",mode,["in0"],
                    util.make_ana_props(in0rng,
                                        get_prop(GLProp.CURRENT_INTERVAL)))
      mult.set_props("mul",mode,["in1"],
                    util.make_ana_props(in1rng,
                                        get_prop(GLProp.CURRENT_INTERVAL)))
      mult.set_props("mul",mode,["coeff"], dig_props)
      mult.set_props("mul",mode,["out"],
                    util.make_ana_props(outrng,
                                        get_prop(GLProp.CURRENT_INTERVAL)))
      mult.set_coeff("mul",mode,'out', scf)

  for mode in vga_modes:
      in0rng,outrng = mode
      # ERRATA: virtual scale of 0.5, but coefficient is scaled by two
      scf = outrng.coeff()/in0rng.coeff()
      get_prop = lambda p : CTX.get(p, mult.name,
                                    'vga',mode,None)

      dig_props = util.make_dig_props(chipcmd.RangeType.MED,\
                                      get_prop(GLProp.DIGITAL_INTERVAL), \
                                      get_prop(GLProp.DIGITAL_QUANTIZE))
      dig_props.set_exclude(get_prop(GLProp.DIGITAL_EXCLUDE));
      dig_props.set_constant()
      mult.set_props("vga",mode,["in0"],
                    util.make_ana_props(in0rng, \
                                        get_prop(GLProp.CURRENT_INTERVAL)
                    ))
      mult.set_props("vga",mode,["in1"],
                    util.make_ana_props(chipcmd.RangeType.MED, \
                                        get_prop(GLProp.CURRENT_INTERVAL)
                    ))
      mult.set_props("vga",mode,["coeff"], dig_props)
      mult.set_props("vga",mode,["out"],
                    util.make_ana_props(outrng, \
                                        get_prop(GLProp.CURRENT_INTERVAL)
                    ))
      mult.set_coeff("vga",mode,'out', scf)



block = Block('multiplier') \
.set_comp_modes(["mul","vga"], glb.HCDCSubset.all_subsets()) \
.add_inputs(props.CURRENT,["in0","in1"]) \
.add_inputs(props.DIGITAL,["coeff"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_op("mul","out",ops.Mult(ops.Var("in0"),ops.Var("in1"))) \
.set_op("vga","out",ops.Mult(ops.Var("coeff"),ops.Var("in0")))

scale_model(block)
continuous_scale_model(block)

block.check()

