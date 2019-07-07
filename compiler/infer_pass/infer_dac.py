import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_datafit as infer_fit

from chip.model import PortModel

def build_config(meta):
  loc = infer_util.to_loc(meta['loc'])
  comp_mode=  "*"
  print(meta.keys())
  scale_mode = infer_util.to_range(meta['rng'])

  out = PortModel('tile_dac',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)

  inp = PortModel('tile_dac',loc,'in', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)

  return inp,out

def infer(obj):
  model_in,model_out = build_config(obj['metadata'])
  bias,noise,in0,in1,out = infer_util \
                           .get_data_by_mode(obj['dataset'],0)
  infer_vis.plot_bias("bias.png",in0,in1,out,bias)
  infer_vis.plot_noise("noise.png",in0,in1,out,noise)
  bnds = infer_fit.infer_model(model_out,in0,in1,out, \
                                     bias,noise,adc=False)
  infer_vis.plot_prediction_error('pred.png',model_out,bnds,
                                  in0,in1,out,bias)

  model_in.bound = bnds['in0']
  yield model_in
  yield model_out
