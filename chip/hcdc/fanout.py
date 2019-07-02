from chip.block import Block, BlockType
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chipcmd.data as chipcmd
from chip.cont import *
import chip.hcdc.globals as glb
import ops.op as ops
import ops.nop as nops
import itertools
import chip.units as units
from chip.hcdc.globals import CTX, GLProp

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


def is_standard(mode):
    return mode == chipcmd.RangeType.MED

def continuous_scale_model(fanout):
    comp_modes = get_comp_modes()
    scale_modes = get_scale_modes()
    for comp_mode in comp_modes:
        csm = ContinuousScaleModel()
        csm.set_baseline((chipcmd.RangeType.MED))
        fanout.set_scale_model(comp_mode,csm)

def scale_model(fanout):
    comp_modes = get_comp_modes()
    scale_modes = get_scale_modes()
    for comp_mode in comp_modes:
        std,nonstd = gutil.partition(is_standard,scale_modes)
        fanout.set_scale_modes(comp_mode,std, \
                               glb.HCDCSubset.all_subsets())
        fanout.set_scale_modes(comp_mode,nonstd, \
                               [glb.HCDCSubset.UNRESTRICTED, \
                                glb.HCDCSubset.EXTENDED2])

        for rng in scale_modes:
            # ERRATA: fanout doesn't scale
            get_prop = lambda p : CTX.get(p, fanout.name,
                                    '*',mode,None)
            ana_props = util.make_ana_props(rng,
                                            get_prop(GLProp.CURRENT_INTERVAL)
            )
            fanout\
                .set_coeff(comp_mode,rng,"out0",1.0) \
                .set_coeff(comp_mode,rng,"out1",1.0) \
                .set_coeff(comp_mode,rng,"out2",1.0)
            fanout\
                .set_props(comp_mode,rng,["out0","out1","out2","in"],
                           ana_props)

    fanout.check()


block = Block('fanout',type=BlockType.COPIER) \
.set_comp_modes(get_comp_modes(), glb.HCDCSubset.all_subsets()) \
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

scale_model(block)
continuous_scale_model(block)
