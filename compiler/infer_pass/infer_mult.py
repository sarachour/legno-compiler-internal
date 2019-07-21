import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_fit as infer_fit
import lab_bench.lib.chipcmd.data as chipdata
from chip.model import PortModel

def build_config(meta):
  loc = infer_util.to_loc(meta['loc'])
  is_vga = infer_util.to_bool(meta['vga'])
  comp_mode = "vga" if is_vga else 'mul'
  if comp_mode == 'vga':
    scale_mode = (infer_util.to_range(meta['ranges']['in0']), \
                  infer_util.to_range(meta['ranges']['out0']))
  else:
    scale_mode = (infer_util.to_range(meta['ranges']['in0']), \
                  infer_util.to_range(meta['ranges']['in1']), \
                  infer_util.to_range(meta['ranges']['out0']))

  out = PortModel('multiplier',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)

  in0 = PortModel('multiplier',loc,'in0', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)
  in1 = PortModel('multiplier',loc,'in1',
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)
  coeff = PortModel('multiplier',loc,'coeff', \
                    comp_mode=comp_mode, \
                    scale_mode=scale_mode)
  return out,in0,in1,coeff


def infer(obj):
  result = build_config(obj['metadata'])
  model_out,model_in0,model_in1,model_coeff = result
  bnds = infer_fit.build_model(model_out,obj['dataset'],0)

  scm = model_out.scale_mode
  #model_out.gain = 1.0
  #bnds['in0'] = [0.90,0.90]
  #bnds['in1'] = [0.90,0.90]
  bnd = infer_util.normalize_bound(bnds['in0'],scm[0])
  model_in0.set_oprange_scale(*bnd)
  if model_out.comp_mode == 'vga':
    model_coeff.set_oprange_scale(*bnds['in1'])
  else:
    bnd = infer_util.normalize_bound(bnds['in1'],scm[1])
    model_in1.set_oprange_scale(*bnd)

  yield model_out
  yield model_in0
  yield model_in1
  yield model_coeff
  #input()
