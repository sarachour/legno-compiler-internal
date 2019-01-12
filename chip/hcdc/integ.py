from chip.block import Block
from chip.phys import PhysicalModel
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
  def cfg_phys_model(phys,scf):
    if util.equals(scf, 1.0):
      new_phys = PhysicalModel.read(util.datapath('integ1x.bb'))
    elif util.equals(scf, 10.0):
      new_phys = PhysicalModel.read(util.datapath('integ1x.bb'))
    elif util.equals(scf, 0.1):
      new_phys = PhysicalModel.read(util.datapath('integ1x.bb'))
    else:
      raise Exception("unknown model: %s" % scf)
    phys.set_to(new_phys)

  modes = get_modes()
  for mode in modes:
    sign,inrng,outrng = mode
    scf = outrng.coeff()/inrng.coeff()
    cfg_phys_model(blk.physical("*",mode,"out"),scf)

  print("[TODO] integ.blackbox")

def scale_model(integ):
  modes = get_modes()
  integ.set_scale_modes("*",modes)
  for mode in modes:
    sign,inrng,outrng = mode
    scf = outrng.coeff()/inrng.coeff()*sign.coeff()
    integ.set_props("*",mode,['in'],util.make_ana_props(inrng,
                                                  glb.ANALOG_MIN, \
                                                  glb.ANALOG_MAX))
    integ.set_props("*",mode,["ic"],util.make_dig_props(chipcmd.RangeType.MED, \
                                                  glb.DAC_MIN,
                                                  glb.DAC_MAX))
    integ.set_props("*",mode,["out"],util.make_ana_props(outrng,
                                                   glb.ANALOG_MIN,
                                                   glb.ANALOG_MAX),\
                    handle=":z")
    integ.set_props("*",mode,["out"],util.make_ana_props(outrng,
                                                   glb.ANALOG_MIN,
                                                   glb.ANALOG_MAX),\
                    handle=":z'")
    integ.set_props("*",mode,["out"],util.make_ana_props(outrng,
                                                   glb.ANALOG_MIN,
                                                   glb.ANALOG_MAX))
    integ.set_coeff("*",mode,"out",scf)


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

