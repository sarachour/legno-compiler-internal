import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_fit as infer_fit

from chip.model import PortModel

def build_config(meta):
  loc = infer_util.to_loc(meta['loc'])
  comp_mode=  "*"
  print(meta.keys())
  scale_mode = infer_util.to_range(meta['rng'])

  out = PortModel('tile_adc',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)

  inp = PortModel('tile_adc',loc,'in', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)

  return scale_mode,inp,out

def infer(obj):
  scm,model_in,model_out = build_config(obj['metadata'])

  bnds = infer_fit.build_model(model_out,obj['dataset'],0,0.04,adc=True)
  bnd = infer_util.normalize_bound(bnds['in0'],scm)
  model_in.set_oprange_scale(*bnd)
  yield model_in
  yield model_out
