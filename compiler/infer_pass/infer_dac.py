import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_fit as infer_fit

from hwlib.model import PortModel

def build_config(meta):
  loc = infer_util.to_loc(meta['loc'])
  comp_mode=  "*"
  print(meta.keys())
  scale_mode = ('pos',infer_util.to_range(meta['rng']))

  out = PortModel('tile_dac',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode,
                  calib_obj=infer_util.CALIB_OBJ)

  inp = PortModel('tile_dac',loc,'in', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode,
                  calib_obj=infer_util.CALIB_OBJ)

  return scale_mode,inp,out

def infer(obj):
  scm,model_in,model_out = build_config(obj['metadata'])

  bnds = infer_fit.build_model(model_out,obj['dataset'],0, \
                               0.02)
  bnd = infer_util.normalize_bound(bnds['in0'],scm[1])
  model_in.set_oprange_scale(*bnd)
  yield model_in
  yield model_out
