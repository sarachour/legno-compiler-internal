from chip.block import Block
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chip_command as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import itertools

def get_modes():
  opts = [
    chipcmd.SignType.options(),
    chipcmd.RangeType.options(),
    chipcmd.RangeType.options()
  ]
  blacklist = [
    (None,chipcmd.RangeType.LOW,chipcmd.RangeType.HIGH),
    (None,chipcmd.RangeType.HIGH,chipcmd.RangeType.LOW)
  ]
  modes = list(util.apply_blacklist(itertools.product(*opts),\
                                    blacklist))
  return modes

def black_box_model(blk):
  print("[TODO] integ.blackbox")

def scale_model(integ):
  modes = get_modes()
  integ.set_scale_modes("*",modes)
  for mode in modes:
    sign,inrng,outrng = mode
    scf = outrng.coeff()/inrng.coeff()*sign.coeff()
    integ.set_info("*",mode,['in'],util.make_ana_props(inrng,
                                                  glb.ANALOG_MIN, \
                                                  glb.ANALOG_MAX))
    integ.set_info("*",mode,["ic"],util.make_dig_props(chipcmd.RangeType.MED, \
                                                  glb.DAC_MIN,
                                                  glb.DAC_MAX))
    integ.set_info("*",mode,["out"],util.make_ana_props(outrng,
                                                   glb.ANALOG_MIN,
                                                   glb.ANALOG_MAX),\
                    handle=":z")
    integ.set_info("*",mode,["out"],util.make_ana_props(outrng,
                                                   glb.ANALOG_MIN,
                                                   glb.ANALOG_MAX),\
                    handle=":z'")
    integ.set_info("*",mode,["out"],util.make_ana_props(outrng,
                                                   glb.ANALOG_MIN,
                                                   glb.ANALOG_MAX))
    integ.set_scale_factor("*",mode,"out",scf)


block = Block('integrator') \
.add_inputs(props.CURRENT,["in","ic"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_op("*","out",
        ops.Integ(ops.Var("in"), ops.Var("ic"),
                  handle=':z'
        )
)
scale_model(block)
black_box_model(block)
block.check()

