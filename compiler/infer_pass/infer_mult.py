import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_datafit as infer_fit

from chip.model import PortModel

def build_config(meta):
  loc = infer_util.to_loc(meta['loc'])
  comp_mode = "vga" if meta['vga'] else mult
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
  model_out,model_in0,model_in1,model_coeff = build_config(obj['metadata'])
  bias,noise,in0,in1,out = infer_util \
                           .get_data_by_mode(obj['dataset'],0)
  infer_vis.plot_bias("bias.png",in0,in1,out,bias)
  infer_vis.plot_noise("noise.png",in0,in1,out,noise)
  bnds = infer_fit.infer_model(model_out,in0,in1,out, \
                                     bias,noise,adc=False)
  infer_vis.plot_prediction_error('pred.png',model_out,bnds,
                                  in0,in1,out,bias)

  model_in0.bound = bnds['in0']
  model_in1.bound = bnds['in1']
  yield model_out
  yield model_in0
  yield model_in1
