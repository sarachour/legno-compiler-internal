import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_datafit as infer_fit

from chip.model import PortModel

def build_config(meta):
  loc = infer_util.to_loc(meta['loc'])
  comp_mode = ( \
                 infer_util.to_sign(meta['invs']['out0']).value,
                 infer_util.to_sign(meta['invs']['out1']).value,
                 infer_util.to_sign(meta['invs']['out2']).value \
  )
  scale_mode = infer_util.to_range(meta['rngs']['in0']).value
  print('fanout[%s]' % loc)
  print(comp_mode)
  print(scale_mode)
  #input()
  out0 = PortModel('fanout',loc,'out0', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)
  out1 = PortModel('fanout',loc,'out1', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)
  out2 = PortModel('fanout',loc,'out2', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)

  inp = PortModel('fanout',loc,'in', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)

  return inp,out0,out1,out2

def infer(obj):
  model_in,model_out0,model_out1,model_out2 = \
                            build_config(obj['metadata'])
  bias,noise,in0,in1,out = infer_util \
                           .get_data_by_mode(obj['dataset'],0)
  infer_vis.plot_bias("bias.png",in0,in1,out,bias)
  infer_vis.plot_noise("noise.png",in0,in1,out,noise)
  print("==== fanout %s ====" % model_in.loc)
  print(obj['metadata'])
  for i0,i1,o,b in zip(in0,in1,out,bias):
    print("in=(%f,%f) out=%f bias=%f" % (i0,i1,o,b))
  bnds0 = infer_fit.infer_model(model_out0,in0,in1,out, \
                                bias,noise,adc=False)
  bias,noise,in0,in1,out = infer_util \
                           .get_data_by_mode(obj['dataset'],1)
  infer_vis.plot_bias("bias.png",in0,in1,out,bias)
  infer_vis.plot_noise("noise.png",in0,in1,out,noise)
  bnds1 = infer_fit.infer_model(model_out1,in0,in1,out, \
                                bias,noise,adc=False)

  bias,noise,in0,in1,out = infer_util \
                           .get_data_by_mode(obj['dataset'],2)
  bnds2 = infer_fit.infer_model(model_out2,in0,in1,out, \
                                bias,noise,adc=False)
  bnds = infer_util.tightest_bounds([bnds0['in0'], \
                                     bnds1['in0'], \
                                     bnds2['in0']])
  model_in.bounds = bnds

  yield model_in
  yield model_out0
  yield model_out1
  yield model_out2
