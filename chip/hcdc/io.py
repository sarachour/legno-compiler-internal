from chip.block import Block, BlockType
import chip.props as props
from chip.phys import PhysicalModel
import chip.units as units
import chip.hcdc.util as util
from chip.cont import *
import lab_bench.lib.chipcmd.data as chipcmd
import chip.hcdc.globals as glb
import ops.op as ops
import itertools

def dac_get_modes():
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

def dac_black_box_model(dac):
   def config_phys_model(phys,rng):
        if rng == chipcmd.RangeType.MED:
            new_phys =  PhysicalModel.read(util.datapath('dac-m.bb'))
        elif rng == chipcmd.RangeType.HIGH:
            new_phys = PhysicalModel.read(util.datapath('dac-h.bb'))
        else:
            raise Exception("unknown physical model: %s" % str(rng))

        phys.set_to(new_phys)

   scale_modes = dac_get_modes()
   for sc in scale_modes:
      _,rng = sc
      config_phys_model(dac.physical('*',sc,"out"),rng)

def dac_continuous_scale_model(dac):
  modes = dac_get_modes()
  csm = ContinuousScaleModel()
  csm.set_baseline((chipcmd.SignType.POS, chipcmd.RangeType.MED))
  out = csm.decl_var(CSMOpVar("out"))
  inp = csm.decl_var(CSMOpVar("in"))
  coeff = csm.decl_var(CSMCoeffVar("out"))
  csm.eq(ops.Mult(ops.Var(inp.varname),
                  ops.Var(coeff.varname)), \
         ops.Var(out.varname))
  inp.set_interval(1.0,1.0)
  coeff.set_interval(1.0,10.0)
  for scm in modes:
     _,scm_o = scm
     expr = ops.Mult(ops.Var('out'),
                     ops.Pow(
                        ops.Mult(ops.Var('in'),ops.Const(2.0)),
                        ops.Const(-1)))

     cstrs = util.build_oprange_cstr([(out,scm_o)],2.0)
     cstrs += util.build_coeff_cstr([(coeff,scm_o.coeff())], expr)
     csm.add_scale_mode(scm, cstrs)

  dac.set_scale_model("*", csm)

def dac_scale_model(dac):
   modes = dac_get_modes()
   dac.set_scale_modes("*",modes)
   for mode in modes:
      sign,rng = mode
      # ERRATA: dac does scale up.
      coeff = sign.coeff()*rng.coeff()*2.0
      digital_props = util.make_dig_props(chipcmd.RangeType.MED,
                                          glb.DAC_MIN,
                                          glb.DAC_MAX,
                                          glb.ANALOG_DAC_SAMPLES
      )
      digital_props.set_min_quantize(digital_props.SignalType.CONSTANT, \
                                     glb.MIN_QUANT_CONST)
      digital_props.set_min_quantize(digital_props.SignalType.DYNAMIC, \
                                     glb.MIN_QUANT_DYNAMIC)

      digital_props.set_continuous(0,glb.MAX_FREQ_DAC,units.khz)
      dac.set_coeff("*",mode,'out', coeff)
      dac.set_props("*",mode,["in"], digital_props)
      dac.set_props("*",mode,["out"],\
                   util.make_ana_props(rng,
                                       glb.ANALOG_MIN,
                                       glb.ANALOG_MAX,
                                       glb.ANALOG_MINSIG_CONST,
                                       glb.ANALOG_MINSIG_DYN))


dac = Block('tile_dac',type=BlockType.DAC) \
.add_outputs(props.CURRENT,["out"]) \
.add_inputs(props.DIGITAL,["in"]) \
.set_op("*","out",ops.Var("in"))
dac_scale_model(dac)
dac_continuous_scale_model(dac)
dac_black_box_model(dac)
dac.check()

def adc_get_modes():
   return [chipcmd.RangeType.HIGH, chipcmd.RangeType.MED]

def adc_black_box_model(adc):
   def config_phys_model(phys,rng):
        if rng == chipcmd.RangeType.MED:
            new_phys =  PhysicalModel.read(util.datapath('adc-m.bb'))
        elif rng == chipcmd.RangeType.HIGH:
            new_phys = PhysicalModel.read(util.datapath('adc-h.bb'))
        else:
            raise Exception("unknown physical model: %s" % str(rng))

        phys.set_to(new_phys)

   scale_modes = dac_get_modes()
   for sc in scale_modes:
      _,rng = sc
      config_phys_model(adc.physical('*',sc,"out"),rng)


def adc_continuous_scale_model(adc):
   modes = adc_get_modes()
   csm = ContinuousScaleModel()
   csm.set_baseline(chipcmd.RangeType.MED)
   out = csm.decl_var(CSMOpVar("out"))
   inp = csm.decl_var(CSMOpVar("in"))
   coeff = csm.decl_var(CSMCoeffVar("out"))
   csm.eq(ops.Mult(ops.Var(inp.varname),
                   ops.Var(coeff.varname)), \
          ops.Var(out.varname))
   inp.set_interval(1.0,10.0)
   coeff.set_interval(0.1,1.0)
   out.set_interval(1.0,1.0)
   for scm_i in modes:
      cstrs = util.build_oprange_cstr([(inp,scm_i)],2.0)
      expr = ops.Mult(
         ops.Var('out'),
         ops.Pow(ops.Mult(ops.Const(0.5),ops.Var('in')),ops.Const(-1)))
      cstrs += util.build_coeff_cstr([(coeff,1.0/scm_i.coeff())], \
                                     expr)
      csm.add_scale_mode(scm_i, cstrs)

   adc.set_scale_model("*", csm)

def adc_scale_model(adc):
   modes = adc_get_modes()
   adc.set_scale_modes("*",modes)
   for mode in modes:
      coeff = (1.0/mode.coeff())*0.5
      analog_props = util.make_ana_props(mode,
                                         glb.ANALOG_MIN,
                                         glb.ANALOG_MAX,
                                         glb.ANALOG_MINSIG_CONST,
                                         glb.ANALOG_MINSIG_DYN)
      #analog_props.set_bandwidth(0,20,units.khz)

      digital_props = util.make_dig_props(chipcmd.RangeType.MED,
                                          glb.DAC_MIN,
                                          glb.DAC_MAX,
                                          glb.ANALOG_DAC_SAMPLES
      )
      digital_props.set_continuous(0,glb.MAX_FREQ_ADC,units.khz)
      digital_props.set_min_quantize(digital_props.SignalType.CONSTANT, \
                                     glb.MIN_QUANT_CONST)
      digital_props.set_min_quantize(digital_props.SignalType.DYNAMIC, \
                                     glb.MIN_QUANT_DYNAMIC)
      adc.set_props("*",mode,["in"],analog_props)
      adc.set_props("*",mode,["out"], digital_props)
      adc.set_coeff("*",mode,'out', coeff)



adc = Block('tile_adc',type=BlockType.ADC) \
.add_outputs(props.DIGITAL,["out"]) \
.add_inputs(props.CURRENT,["in"]) \
.set_op("*","out",ops.Var("in")) \
.set_props("*","*",["out"],None) \
.set_props("*","*",["in"],None) \
.set_coeff("*","*","out",0.5)
adc_scale_model(adc)
adc_continuous_scale_model(adc)
adc_black_box_model(adc)
adc.check()
