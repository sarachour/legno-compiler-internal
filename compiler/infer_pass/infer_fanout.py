import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_fit as infer_fit

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

  bnds0 = infer_fit.build_model(model_out0,obj['dataset'],0)
  bnds1 = infer_fit.build_model(model_out1,obj['dataset'],1)
  bnds2 = infer_fit.build_model(model_out2,obj['dataset'],2)
  bnds = infer_util.tightest_bounds([bnds0['in0'], \
                                     bnds1['in0'], \
                                     bnds2['in0']])
  model_in.set_oprange_scale(*bnds)
  # this causes scaling issues because there aren't enough degrees of freedom.
  #model_out0.gain = 1.0
  #model_out1.gain = 1.0
  #model_out2.gain = 1.0
  yield model_in
  yield model_out0
  yield model_out1
  yield model_out2
