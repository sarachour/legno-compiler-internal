from chip.block import Block
import chip.props as props
import chip.units as units
import chip.hcdc.util as util
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


def continuous_scale_model(integ):
  m = chipcmd.RangeType.MED
  comp_modes = get_comp_modes()
  scale_modes = get_scale_modes()
  for comp_mode in comp_modes:
    csm = cont.ContinuousScaleModel()
    csm.set_baseline((m,m))
    op_in = cont.decl_in(csm,'in')
    op_ic = cont.decl_in(csm,'ic')
    op_out, c_out = cont.decl_out(csm,'out')

    op_inI,c_inI = cont.decl_out(csm,'out',':z\'')
    op_icI,c_icI = cont.decl_out(csm,'out',':z[0]')
    op_outI,c_outI = cont.decl_out(csm,'out',':z')

    c_in2out = csm.decl_var(cont.CSMCoeffVar('comp_scale'))

    cont.equals(csm, [c_inI, c_in2out])
    cont.equals(csm, [c_icI, op_out, op_outI])
    csm.eq(ops.Var(c_in2out.varname), \
           ops.Div(
             ops.Var(op_in.varname),
             ops.Var(op_out.varname)
           ))


    csm.eq(
      ops.Mult(
        ops.Var(op_outI.varname),
        ops.Var(c_outI.varname)
      ),
      ops.Var(op_out.varname)
    )
    csm.eq(
      ops.Mult(
        ops.Var(op_in.varname),
        ops.Var(c_inI.varname)
      ),
      ops.Var(op_inI.varname)
    )
    csm.eq(
      ops.Mult(
        ops.Var(op_ic.varname),
        ops.Var(c_icI.varname)
      ),
      ops.Var(op_icI.varname)
    )


    for scm in scale_modes:
      scm_i, scm_o = scm
      coeff = scm_o.coeff()/scm_i.coeff()
      csm.discrete.add_mode(scm)
      csm.discrete.add_cstr(scm,op_in,scm_i.coeff())
      csm.discrete.add_cstr(scm,op_ic,1.0)
      csm.discrete.add_cstr(scm,c_out,1.0)
      csm.discrete.add_cstr(scm,c_icI,scm_o.coeff())
      csm.discrete.add_cstr(scm,op_out,scm_o.coeff())
      csm.discrete.add_cstr(scm,c_in2out,coeff)

    integ.set_scale_model(comp_mode,csm)

def scale_model(integ):
  comp_modes = get_comp_modes()
  scale_modes = get_scale_modes()
  for comp_mode in comp_modes:
    integ.set_scale_modes(comp_mode,scale_modes)
    for scale_mode in scale_modes:
      get_prop = lambda p : CTX.get(p, integ.name,
                                    comp_mode,scale_mode,None)
      inrng,outrng = scale_mode
      analog_in = util.make_ana_props(inrng, \
                                      get_prop(GLProp.CURRENT_INTERVAL))
      analog_in.set_bandwidth(0,get_prop(GLProp.MAX_FREQ),units.khz)

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
      scf_ic = outrng.coeff()
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
block.check()

