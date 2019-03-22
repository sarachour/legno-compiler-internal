from chip.block import Block
from chip.phys import PhysicalModel
import chip.props as props
import chip.hcdc.util as util
import chip.units as units
from chip.cont import *
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import ops.nop as nops
import itertools

# 10.0 >= coeff >= 0.1
# 10.0 >= in0 >= 0.1
# 10.0 >= in1 >= 0.1
# 10.0 >= out >= 0.1
# out = in0*in1*coeff
# 

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
    (chipcmd.RangeType.LOW,chipcmd.RangeType.LOW,chipcmd.RangeType.HIGH),
    (chipcmd.RangeType.MED,chipcmd.RangeType.LOW,chipcmd.RangeType.HIGH),
    (chipcmd.RangeType.LOW,chipcmd.RangeType.MED,chipcmd.RangeType.HIGH),
    (chipcmd.RangeType.HIGH,chipcmd.RangeType.HIGH,chipcmd.RangeType.LOW),
    (chipcmd.RangeType.HIGH,chipcmd.RangeType.MED,chipcmd.RangeType.LOW),
    (chipcmd.RangeType.MED,chipcmd.RangeType.HIGH,chipcmd.RangeType.LOW)

  ]
  vga_modes = list(util.apply_blacklist(itertools.product(*opts_vga),
                                   blacklist_vga))
  mul_modes = list(util.apply_blacklist(itertools.product(*opts_def),
                                   blacklist_mult))
  return vga_modes,mul_modes

def black_box_model(mult):
  def config_phys(phys,rng,scf,vga=False):
    base = "mult" if not vga else "vga"
    if rng == chipcmd.RangeType.MED:
      base += "-m"
    elif rng == chipcmd.RangeType.LOW:
      base += "-l"
    elif rng == chipcmd.RangeType.HIGH:
      base += "-h"

    if util.equals(scf, 1.0):
      new_phys = PhysicalModel.read(util.datapath('%s1x.bb' % base))
    elif util.equals(scf, 10.0) or util.equals(scf, 100.0):
      new_phys = PhysicalModel.read(util.datapath('%s10x.bb' % base))
    elif util.equals(scf, 0.1) or util.equals(scf, 0.01):
      new_phys = PhysicalModel.read(util.datapath('%s01x.bb' % base))
    else:
      raise Exception("unknown scf: %s" % scf)

    phys.set_to(new_phys)

  vga_modes,mul_modes = get_modes()
  for mode in vga_modes:
    in0rng,outrng = mode
    scf = outrng.coeff()/in0rng.coeff()
    phys = mult.physical('vga',mode,'out')
    config_phys(phys,outrng,scf,vga=True)

  for mode in mul_modes:
    in0rng,in1rng,outrng = mode
    scf = outrng.coeff()/(in0rng.coeff()*in1rng.coeff())
    phys = mult.physical('mul',mode,'out')
    config_phys(phys,outrng,scf)



def continuous_scale_model_vga(mult):
  vga_modes,_= get_modes()
  m = chipcmd.RangeType.MED

  csm = ContinuousScaleModel()
  csm.set_baseline((m,m))
  op_in0 = csm.decl_var(CSMOpVar("in0"))
  op_coeff = csm.decl_var(CSMOpVar("coeff"))
  op_out = csm.decl_var(CSMOpVar("out"))
  scf_tf = csm.decl_var(CSMCoeffVar("out"))

  for csmvar in [scf_tf]:
    #scf_tf.set_interval(0.01,100.0)
    csmvar.set_interval(0.1,10.0)
    #csmvar.set_interval(1.0,1.0)


  for csmvar in [op_in0,op_out]:
    csmvar.set_interval(0.1,10.0)


  for csmvar in [op_coeff]:
    csmvar.set_interval(1.0,1.0)

  csm.eq(ops.Mult(ops.Var(op_in0.varname),
                  ops.Var(scf_tf.varname)),
         ops.Var(op_out.varname))

  for scm in vga_modes:
    scm_i, scm_o = scm
    coeff = scm_o.coeff()/scm_i.coeff()
    #if coeff != 1.0:
    #  continue

    expr = ops.Mult(ops.Var('out'), ops.Pow(
      ops.Mult(ops.Var('coeff'),ops.Var('in0')), \
      ops.Const(-1)))

    cstrs = util.build_oprange_cstr([(op_in0,scm_i), \
                                   (op_out,scm_o)],2.0)
    cstrs += util.build_coeff_cstr([(scf_tf,coeff)],expr)
    csm.add_scale_mode(scm,cstrs)

  mult.set_scale_model('vga',csm)

def continuous_scale_model_mult(mult):
  _,mul_modes = get_modes()
  m = chipcmd.RangeType.MED

  csm = ContinuousScaleModel()
  csm.set_baseline((m,m,m))
  in0 = csm.decl_var(CSMOpVar("in0"))
  in1 = csm.decl_var(CSMOpVar("in1"))
  out = csm.decl_var(CSMOpVar("out"))
  scf_tf = csm.decl_var(CSMCoeffVar("out"))

  csm.eq(ops.Mult(ops.Mult(ops.Var(in0.varname),
                           ops.Var(in1.varname)),
                  ops.Var(scf_tf.varname)), \
         ops.Var(out.varname))

  for csmvar in [scf_tf]:
    #scf_tf.set_interval(0.01,100.0)
    csmvar.set_interval(0.1,10.0)
    #csmvar.set_interval(1.0,1.0)

  for csmvar in [in0,in1,out]:
    csmvar.set_interval(0.1,10.0)

  for scm in mul_modes:
    scm_i0,scm_i1,scm_o = scm
    coeff =scm_o.coeff()/(scm_i0.coeff()*scm_i1.coeff())
    #if coeff != 1.0:
    #  continue
    expr = ops.Mult(ops.Mult(ops.Const(1/0.5), ops.Var('out')), ops.Pow(
      ops.Mult(ops.Var('in0'),ops.Var('in1')),ops.Const(-1)))
    cstrs = util.build_oprange_cstr([(in0,scm_i0), \
                                         (in1,scm_i1), \
                                         (out,scm_o)],2.0)
    cstrs += util.build_coeff_cstr([(scf_tf,coeff)],expr)
    csm.add_scale_mode(scm,cstrs)

  mult.set_scale_model('mul',csm)

def continuous_scale_model(mult):
  continuous_scale_model_vga(mult)
  continuous_scale_model_mult(mult)


def scale_model(mult):
  vga_modes,mul_modes = get_modes()
  mult.set_scale_modes("mul",mul_modes)
  mult.set_scale_modes("vga",vga_modes)
  for mode in mul_modes:
      in0rng,in1rng,outrng = mode
      # ERRATA: virtual scale of 0.5
      scf = 0.5*outrng.coeff()/(in0rng.coeff()*in1rng.coeff())
      dig_props = util.make_dig_props(chipcmd.RangeType.MED, \
                                        glb.DAC_MIN,
                                        glb.DAC_MAX,
                                        glb.ANALOG_DAC_SAMPLES)
      dig_props.set_min_quantize(dig_props.SignalType.CONSTANT, glb.MIN_QUANT_CONST)
      dig_props.set_constant()
      mult.set_props("mul",mode,["in0"],
                    util.make_ana_props(in0rng,
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX,
                                        glb.ANALOG_MINSIG_CONST,
                                        glb.ANALOG_MINSIG_DYN))
      mult.set_props("mul",mode,["in1"],
                    util.make_ana_props(in1rng,
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX,
                                        glb.ANALOG_MINSIG_CONST,
                                        glb.ANALOG_MINSIG_DYN))
      mult.set_props("mul",mode,["coeff"], dig_props)
      mult.set_props("mul",mode,["out"],
                    util.make_ana_props(outrng,
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX,
                                        glb.ANALOG_MINSIG_CONST,
                                        glb.ANALOG_MINSIG_DYN))
      mult.set_coeff("mul",mode,'out', scf)

  for mode in vga_modes:
      in0rng,outrng = mode
      # ERRATA: virtual scale of 0.5, but coefficient is scaled by two
      scf = outrng.coeff()/in0rng.coeff()
      dig_props = util.make_dig_props(chipcmd.RangeType.MED,\
                                      glb.DAC_MIN,
                                      glb.DAC_MAX, \
                                      glb.ANALOG_DAC_SAMPLES)
      dig_props.set_min_quantize(dig_props.SignalType.CONSTANT, glb.MIN_QUANT_CONST)
      dig_props.set_constant()
      mult.set_props("vga",mode,["in0"],
                    util.make_ana_props(in0rng, \
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX,
                                        glb.ANALOG_MINSIG_CONST,
                                        glb.ANALOG_MINSIG_DYN))
      mult.set_props("vga",mode,["in1"],
                    util.make_ana_props(chipcmd.RangeType.MED, \
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX,
                                        glb.ANALOG_MINSIG_CONST,
                                        glb.ANALOG_MINSIG_DYN))
      mult.set_props("vga",mode,["coeff"], dig_props)
      mult.set_props("vga",mode,["out"],
                    util.make_ana_props(outrng, \
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX,
                                        glb.ANALOG_MINSIG_CONST,
                                        glb.ANALOG_MINSIG_DYN))
      mult.set_coeff("vga",mode,'out', scf)


block = Block('multiplier') \
.set_comp_modes(["mul","vga"]) \
.add_inputs(props.CURRENT,["in0","in1"]) \
.add_inputs(props.DIGITAL,["coeff"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_op("mul","out",ops.Mult(ops.Var("in0"),ops.Var("in1"))) \
.set_op("vga","out",ops.Mult(ops.Var("coeff"),ops.Var("in0")))

scale_model(block)
continuous_scale_model(block)
black_box_model(block)

block.check()

