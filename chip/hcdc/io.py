from chip.block import Block, BlockType
import chip.props as props
import chip.hcdc.util as util
import lab_bench.lib.chip_command as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import itertools

def get_modes():
   opts = [
      [chipcmd.SignType.POS],
      chipcmd.RangeType.options()
   ]
   blacklist = [
      (None,chipcmd.RangeType.LOW)
   ]
   modes = list(util.apply_blacklist(itertools.product(*opts),
                                     blacklist))
   return modes

def black_box_model(dac):
   print("[TODO] dac.blackbox")

def scale_model(dac):
   modes = get_modes()
   dac.set_scale_modes("*",modes)
   for mode in modes:
      sign,rng = mode
      coeff = sign.coeff()*rng.coeff()*2.0
      dac.set_coeff("*",mode,'out', coeff)
      dac.set_props("*",mode,["in"], \
                   util.make_dig_props(chipcmd.RangeType.MED,
                                  glb.DAC_MIN,
                                  glb.DAC_MAX))

      dac.set_props("*",mode,["out"],\
                   util.make_ana_props(rng,
                                       glb.ANALOG_MIN,
                                       glb.ANALOG_MAX))


dac = Block('tile_dac',type=BlockType.DAC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.DIGITAL,["in"]) \
.set_op("*","out",ops.Var("in"))
scale_model(dac)
black_box_model(dac)
dac.check()

adc = Block('tile_adc',type=BlockType.ADC) \
.add_outputs(props.DIGITAL,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["out"],None) \
.set_props("*","*",["in"],None) \
.set_coeff("*","*","out",1.0)
scale_model(adc)
black_box_model(adc)
adc.check()
