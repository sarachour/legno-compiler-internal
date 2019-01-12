from chip.block import Block
from chip.phys import PhysicalModel
import chip.props as props
import chip.hcdc.util as util
import chip.units as units
import lab_bench.lib.chip_command as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import ops.nop as nops
import itertools

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
  def config_phys(phys,scf):
    if util.equals(scf, 1.0):
      new_phys = PhysicalModel.read(util.datapath('mult1x.bb'))
    elif util.equals(scf, 10.0) or util.equals(scf, 100.0):
      new_phys = PhysicalModel.read(util.datapath('mult10x.bb'))
    elif util.equals(scf, 0.1) or util.equals(scf, 0.01):
      new_phys = PhysicalModel.read(util.datapath('mult1x.bb'))
    else:
      raise Exception("unknown scf: %s" % scf)

    phys.set_to(new_phys)

  vga_modes,mul_modes = get_modes()
  for mode in vga_modes:
    in0rng,outrng = mode
    scf = outrng.coeff()/in0rng.coeff()
    phys = mult.physical('vga',mode,'out')
    config_phys(phys,scf)

  for mode in mul_modes:
    in0rng,in1rng,outrng = mode
    scf = outrng.coeff()/(in0rng.coeff()*in1rng.coeff())
    phys = mult.physical('mul',mode,'out')
    config_phys(phys,scf)


  print("[TODO] mult.blackbox")

def scale_model(mult):
  vga_modes,mul_modes = get_modes()
  mult.set_scale_modes("mul",mul_modes)
  mult.set_scale_modes("vga",vga_modes)
  for mode in mul_modes:
      in0rng,in1rng,outrng = mode
      scf = outrng.coeff()/(in0rng.coeff()*in1rng.coeff())
      mult.set_props("mul",mode,["in0"],
                    util.make_ana_props(in0rng,
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX))
      mult.set_props("mul",mode,["in1"],
                    util.make_ana_props(in1rng,
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX))
      mult.set_props("mul",mode,["coeff"],
                    util.make_dig_props(chipcmd.RangeType.MED, \
                                        glb.DAC_MIN,
                                        glb.DAC_MAX))
      mult.set_props("mul",mode,["out"],
                    util.make_ana_props(outrng,
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX))
      mult.set_coeff("mul",mode,'out', scf)

  for mode in vga_modes:
      in0rng,outrng = mode
      scf = outrng.coeff()/in0rng.coeff()
      mult.set_props("vga",mode,["in0"],
                    util.make_ana_props(in0rng, \
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX))
      mult.set_props("vga",mode,["in1"],
                    util.make_ana_props(chipcmd.RangeType.MED, \
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX))
      mult.set_props("vga",mode,["coeff"],
                    util.make_dig_props(chipcmd.RangeType.MED,\
                                        glb.DAC_MIN,
                                        glb.DAC_MAX))
      mult.set_props("vga",mode,["out"],
                    util.make_ana_props(outrng, \
                                        glb.ANALOG_MIN,
                                        glb.ANALOG_MAX))
      mult.set_coeff("vga",mode,'out', scf)


block = Block('multiplier') \
.set_comp_modes(["mul","vga"]) \
.add_inputs(props.CURRENT,["in0","in1"]) \
.add_inputs(props.DIGITAL,["coeff"]) \
.add_outputs(props.CURRENT,["out"]) \
.set_op("mul","out",ops.Mult(ops.Var("in0"),ops.Var("in1"))) \
.set_op("vga","out",ops.Mult(ops.Var("coeff"),ops.Var("in0")))

scale_model(block)
black_box_model(block)

block.check()

