from chip.block import Block
from chip.phys import PhysicalModel
import chip.props as props
import chip.units as units
import chip.hcdc.util as util
from chip.cont import *

import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
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

def black_box_model(blk):
  def cfg_phys_model(phys,rng,scf):
    base = "integ"
    if rng == chipcmd.RangeType.MED:
      base += "-m"
    elif rng == chipcmd.RangeType.LOW:
      base += "-l"
    elif rng == chipcmd.RangeType.HIGH:
      base += "-h"

    if util.equals(scf, 1.0):
      new_phys = PhysicalModel.read(util.datapath('%s1x.bb' % base))
    elif util.equals(scf, 10.0):
      new_phys = PhysicalModel.read(util.datapath('%s10x.bb' % base))
    elif util.equals(scf, 0.1):
      new_phys = PhysicalModel.read(util.datapath('%s01x.bb' % base))
    else:
      raise Exception("unknown model: %s" % scf)
    phys.set_to(new_phys)

  comp_modes = get_comp_modes()
  scale_modes = get_scale_modes()
  for comp_mode in comp_modes:
    for scale_mode in scale_modes:
      inrng,outrng = scale_mode
      scf = outrng.coeff()/inrng.coeff()
      ph = blk.physical(comp_mode,scale_mode,"out")
      cfg_phys_model(ph,outrng,scf)

  print("[TODO] integ.blackbox")

def continuous_scale_model(integ):
  m = chipcmd.RangeType.MED
  comp_modes = get_comp_modes()
  for comp_mode in comp_modes:
    csm = ContinuousScaleModel()
    csm.set_baseline((m,m))
    deriv = csm.decl_var(CSMOpVar("in"))
    out = csm.decl_var(CSMOpVar("out"))

    coeff = csm.decl_var(CSMCoeffVar("out"))
    coeff_deriv = csm.decl_var(CSMCoeffVar("out",handle=':z\''))
    coeff_deriv = csm.decl_var(CSMCoeffVar("out",handle=':z'))
    coeff_ic = csm.decl_var(CSMCoeffVar("out",handle=':z[0]'))

    ic_int = csm.decl_var(CSMOpVar("out",handle=':z[0]'))
    deriv_int = csm.decl_var(CSMOpVar("out",handle=':z\''))
    out_int = csm.decl_var(CSMOpVar("out",handle=':z'))
    csm.eq(ops.Mult(ops.Var(coeff.varname),
                    ops.Var(deriv.varname)), ops.Var(out.varname))
    print("[TODO]: integrator constraints")
    csm.eq(ops.Var(coeff_ic.varname), ops.Var(coeff.varname))
    csm.eq(ops.Var(ic_int.varname), ops.Var(out.varname))
    csm.eq(ops.Var(out_int.varname), ops.Var(out.varname))
    csm.eq(ops.Var(deriv_int.varname), ops.Var(deriv.varname))

    for csmvar in [deriv,out,ic_int,deriv_int,out_int,coeff]:
      csmvar.set_interval(0.1,10.0)

    integ.set_scale_model(comp_mode,csm)

def scale_model(integ):
  comp_modes = get_comp_modes()
  scale_modes = get_scale_modes()
  for comp_mode in comp_modes:
    integ.set_scale_modes(comp_mode,scale_modes)
    for scale_mode in scale_modes:
      inrng,outrng = scale_mode
      analog_in = util.make_ana_props(inrng,
                                      glb.ANALOG_MIN, \
                                      glb.ANALOG_MAX, \
                                      glb.ANALOG_MINSIG)
      analog_in.set_bandwidth(0,20,units.khz)
      dig_props = util.make_dig_props(chipcmd.RangeType.MED, \
                                          glb.DAC_MIN, \
                                          glb.DAC_MAX, \
                                          glb.MAX_DAC_ERROR_CONST,
                                          glb.ANALOG_DAC_SAMPLES)
      dig_props.set_constant()
      integ.set_props(comp_mode,scale_mode,['in'],analog_in)
      integ.set_props(comp_mode,scale_mode,["ic"], dig_props)
      integ.set_props(comp_mode,scale_mode,["out"],\
                      util.make_ana_props(outrng,
                                          glb.ANALOG_MIN,
                                          glb.ANALOG_MAX,
                                          glb.ANALOG_MINSIG),\
                      handle=":z[0]")
      integ.set_props(comp_mode,scale_mode,["out"],\
                      util.make_ana_props(outrng,
                                          glb.ANALOG_MIN,
                                          glb.ANALOG_MAX,
                                          glb.ANALOG_MINSIG),\
                      handle=":z")
      integ.set_props(comp_mode,scale_mode,["out"],
                      util.make_ana_props(inrng,
                                          glb.ANALOG_MIN,
                                          glb.ANALOG_MAX,
                                          glb.ANALOG_MINSIG),\
                      handle=":z'")
      integ.set_props(comp_mode,scale_mode,["out"],
                      util.make_ana_props(outrng,
                                          glb.ANALOG_MIN,
                                          glb.ANALOG_MAX,
                                          glb.ANALOG_MINSIG))

      scf_inout = outrng.coeff()/inrng.coeff()
      scf_ic = outrng.coeff()*2.0
      integ.set_coeff(comp_mode,scale_mode,"out",scf_inout,handle=':z\'')
      integ.set_coeff(comp_mode,scale_mode,"out",scf_ic,':z[0]')
      integ.set_coeff(comp_mode,scale_mode,"out",1.0,handle=':z')
      integ.set_coeff(comp_mode,scale_mode,"out",1.0)

block = Block('integrator') \
.set_comp_modes(get_comp_modes()) \
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
black_box_model(block)
block.check()

