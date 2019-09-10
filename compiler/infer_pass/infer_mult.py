import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_fit as infer_fit
import lab_bench.lib.chipcmd.data as chipdata
import hwlib.hcdc.enums as spec_enums
from hwlib.model import PortModel

def build_config(meta):
  loc = infer_util.to_loc(meta['loc'])
  is_vga = infer_util.to_bool(meta['vga'])
  comp_mode = "vga" if is_vga else 'mul'
  if comp_mode == 'vga':
    scale_mode = (infer_util.to_range(meta['ranges']['in0']), \
                  infer_util.to_range(meta['ranges']['out0']))
    _,out = scale_mode
    max_unc = out.coeff()*0.04

  else:
    scale_mode = (infer_util.to_range(meta['ranges']['in0']), \
                  infer_util.to_range(meta['ranges']['in1']), \
                  infer_util.to_range(meta['ranges']['out0']))
    _,_,out = scale_mode
    max_unc = out.coeff()*0.05

  out = PortModel('multiplier',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode,
                  calib_obj=infer_util.CALIB_OBJ)

  in0 = PortModel('multiplier',loc,'in0', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode,
                  calib_obj=infer_util.CALIB_OBJ)
  in1 = PortModel('multiplier',loc,'in1',
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode,
                  calib_obj=infer_util.CALIB_OBJ)
  coeff = PortModel('multiplier',loc,'coeff', \
                    comp_mode=comp_mode, \
                    scale_mode=scale_mode,
                    calib_obj=infer_util.CALIB_OBJ)
  return scale_mode,max_unc,out,in0,in1,coeff


def infer(obj):
  result = build_config(obj['metadata'])
  scm,max_unc,model_out,model_in0,model_in1,model_coeff = result
  bnds = infer_fit.build_model(model_out,obj['dataset'],0,max_unc)
  cm = model_out.comp_mode
  if cm == 'vga':
    sci,sco = scm
    scale = sco.coeff()/sci.coeff()
    model_in0.bias_uncertainty = model_out.bias_uncertainty/scale
    bnd = infer_util.normalize_bound(bnds['in0'],scm[0])
    model_in0.set_oprange_scale(*bnd)
    bnd = infer_util.normalize_bound(bnds['in1'],spec_enums.RangeType.MED)
    model_coeff.set_oprange_scale(*bnd)
  else:
    sci0,sci1,sco = scm
    scale0 = sco.coeff()/(sci0.coeff())
    model_in0.bias_uncertainty = model_out.bias_uncertainty/scale0
    bnd = infer_util.normalize_bound(bnds['in0'],scm[0])
    model_in0.set_oprange_scale(*bnd)
    scale1 = sco.coeff()/(sci1.coeff())
    model_in1.bias_uncertainty = model_out.bias_uncertainty/scale1
    bnd = infer_util.normalize_bound(bnds['in1'],scm[1])
    model_in1.set_oprange_scale(*bnd)

  yield model_out
  yield model_in0
  yield model_in1
  yield model_coeff
  #input()
