from chip.block import Block, BlockType
from chip.phys import PhysicalModel
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chip_command as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import ops.nop as nops
import itertools
import chip.units as units

def get_modes():
    opts = [
        chipcmd.SignType.options(),
        chipcmd.SignType.options(),
        chipcmd.SignType.options(),
        chipcmd.RangeType.options()
    ]
    blacklist = [
        (None,None,None,chipcmd.RangeType.LOW)
    ]
    modes = list(util.apply_blacklist(itertools.product(*opts),
                                      blacklist))
    return modes

def blackbox_model(fanout):
    def config_phys_model(phys,rng):
        if rng == chipcmd.RangeType.MED:
            new_phys =  PhysicalModel.read(util.datapath('fanout1x.bb'))
        elif rng == chipcmd.RangeType.HIGH:
            new_phys = PhysicalModel.read(util.datapath('fanout10x.bb'))
        else:
            raise Exception("unknown physical model")

        phys.set_to(new_phys)

    modes = get_modes()
    print("[TODO]: fanout.blackbox")
    for mode in modes:
        _,_,_,rng = mode
        config_phys_model(fanout.physical("*",mode,"out0"),rng)
        config_phys_model(fanout.physical("*",mode,"out1"),rng)
        config_phys_model(fanout.physical("*",mode,"out2"),rng)

def scale_model(fanout):
    modes = get_modes()
    fanout.set_scale_modes("*",modes)
    for mode in modes:
        inv0,inv1,inv2,rng = mode
        fanout\
            .set_coeff("*",mode,"out0",inv0.coeff()) \
            .set_coeff("*",mode,"out1",inv1.coeff()) \
            .set_coeff("*",mode,"out2",inv2.coeff())
        fanout\
            .set_props("*",mode,["out0","out1","out2","in"],
                      util.make_ana_props(rng,
                                          glb.ANALOG_MIN, \
                                          glb.ANALOG_MAX))

    fanout.check()


block = Block('fanout',type=BlockType.COPIER) \
.add_outputs(props.CURRENT,["out1","out2","out0"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out0",ops.Var("in")) \
.set_copy("*","out1","out0") \
.set_copy("*","out2","out0")
blackbox_model(block)
scale_model(block)
