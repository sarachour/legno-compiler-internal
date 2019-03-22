from chip.block import Block, BlockType
from chip.phys import PhysicalModel
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
from chip.cont import *
import chip.hcdc.globals as glb
import ops.op as ops
import ops.nop as nops
import itertools
import chip.units as units

def get_comp_modes():
    comp_options = [chipcmd.SignType.options(),
                    chipcmd.SignType.options(),
                    chipcmd.SignType.options()]


    modes = list(itertools.product(*comp_options))
    return modes

def get_scale_modes():
    blacklist = [
        chipcmd.RangeType.LOW
    ]
    return list(util.apply_blacklist(chipcmd.RangeType.options(), \
                                     blacklist))

def blackbox_model(fanout):
    def config_phys_model(phys,rng):
        if rng == chipcmd.RangeType.MED:
            new_phys =  PhysicalModel.read(util.datapath('fanout-m.bb'))
        elif rng == chipcmd.RangeType.HIGH:
            new_phys = PhysicalModel.read(util.datapath('fanout-h.bb'))
        else:
            raise Exception("unknown physical model: %s" % rng)

        phys.set_to(new_phys)

    comp_modes = get_comp_modes()
    scale_modes = get_scale_modes()
    for c_mode in comp_modes:
        for rng in scale_modes:
            config_phys_model(fanout.physical(c_mode,rng,"out0"),rng)
            config_phys_model(fanout.physical(c_mode,rng,"out1"),rng)
            config_phys_model(fanout.physical(c_mode,rng,"out2"),rng)

def continuous_scale_model(fanout):
    comp_modes = get_comp_modes()
    scale_modes = get_scale_modes()
    for comp_mode in comp_modes:
        csm = ContinuousScaleModel()
        csm.set_baseline((chipcmd.RangeType.MED))
        inp = csm.decl_var(CSMOpVar("in"))
        inp.set_interval(1.0,10.0)
        for i in range(0,3):
            out = csm.decl_var(CSMOpVar("out%d" % i))
            coeff = csm.decl_var(CSMCoeffVar("out%d" % i))
            out.set_interval(1.0,10.0)
            coeff.set_interval(1.0,1.0)
            csm.eq(ops.Var(out.varname), ops.Var(inp.varname))

        for scm in scale_modes:
            cstrs = util.build_oprange_cstr([(inp,scm)],2.0)
            csm.add_scale_mode(scm,cstrs)

        fanout.set_scale_model(comp_mode,csm)

def scale_model(fanout):
    comp_modes = get_comp_modes()
    scale_modes = get_scale_modes()
    for comp_mode in comp_modes:
        fanout.set_scale_modes(comp_mode,scale_modes)
        for rng in scale_modes:
            # ERRATA: fanout doesn't scale
            fanout\
                .set_coeff(comp_mode,rng,"out0",1.0) \
                .set_coeff(comp_mode,rng,"out1",1.0) \
                .set_coeff(comp_mode,rng,"out2",1.0)
            fanout\
                .set_props(comp_mode,rng,["out0","out1","out2","in"],
                        util.make_ana_props(rng,
                                            glb.ANALOG_MIN, \
                                            glb.ANALOG_MAX,
                                            glb.ANALOG_MINSIG_CONST,
                                            glb.ANALOG_MINSIG_DYN))

    fanout.check()


block = Block('fanout',type=BlockType.COPIER) \
.set_comp_modes(get_comp_modes()) \
.add_outputs(props.CURRENT,["out1","out2","out0"]) \
.add_inputs(props.CURRENT,["in"])

do_sign = lambda mode: ops.Var("in") \
          if mode == chipcmd.SignType.POS \
          else ops.Mult(ops.Var("in"),ops.Const(-1))

for mode in get_comp_modes():
    sign0,sign1,sign2 = mode
    block.set_op(mode,"out0",do_sign(sign0))
    block.set_op(mode,"out1",do_sign(sign1))
    block.set_op(mode,"out2",do_sign(sign2))

blackbox_model(block)
scale_model(block)
continuous_scale_model(block)
