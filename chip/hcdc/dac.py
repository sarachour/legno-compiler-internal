
def get_modes():
   opts = [
        chipcmd.SignType.options(),
        chipcmd.RangeType.options()
    ]
    blacklist = [
        (None,chipcmd.RangeType.LOW)
    ]
    modes = list(apply_blacklist(itertools.product(*opts),blacklist))
    return modes

def black_box_model(dac):
  raise Exception("unimplemented")

def scale_model(dac):
  modes = get_modes()
  dac.set_scale_modes("*",modes)
  for mode in modes:
    sign,rng = mode
    coeff = sign.coeff()*rng.coeff()*2.0
    dac.set_scale_factor("*",mode,'out', coeff)
    dac.set_info("*",mode,["in"], \
                 make_dig_props(chipcmd.RangeType.MED,DAC_MIN,DAC_MAX))
    dac.set_info("*",mode,["out"],make_ana_props(rng,ANALOG_MIN,ANALOG_MAX))



dac = Block('tile_dac',type=Block.DAC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.DIGITAL,["in"]) \
.set_op("*","out",ops.Var("in"))
scale_model(block)
block.check()

adc = Block('tile_adc',type=Block.ADC) \
.add_outputs(props.DIGITAL,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_info("*","*",["out"],None) \
.set_info("*","*",["in"],None) \
.set_scale_factor("*","*","out",1.0) \
.check()
