import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_datafit as infer_fit

from chip.model import PortModel

def build_config(meta):
  loc = infer_util.to_loc(meta['loc'])
  print(meta.keys())
  comp_mode =  infer_util.to_sign(meta['invs']['out0'])
  scale_mode = ( \
                 infer_util.to_range(meta['ranges']['in0']), \
                 infer_util.to_range(meta['ranges']['out0']) \
  )
  inp = PortModel('integrator',loc,'in', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)
  out = PortModel('integrator',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)
  out_z0 = PortModel('integrator',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode, \
                  handle='z[0]')
  out_zp = PortModel('integrator',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode, \
                  handle='z\'')
  out_z = PortModel('integrator',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode, \
                  handle='z')

  ic = PortModel('integrator',loc,'ic', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)
  return inp,ic,out,out_z,out_z0,out_zp

def infer(obj):
  model_in,model_ic,model_out, \
    out_z,out_z0,out_zp = build_config(obj['metadata'])
  bias,noise,in0,in1,out = infer_util \
                           .get_data_by_mode(obj['dataset'],0)
  infer_vis.plot_bias("bias.png",in0,in1,out,bias)
  infer_vis.plot_noise("noise.png",in0,in1,out,noise)
  bnds_ic = infer_fit.infer_model(out_z0,in0,in1,out, \
                                  bias,noise,adc=False)

  for o,b in zip(out,bias):
    print("out=%s bias=%s" % (o,b))
  input("ic")
  bias,noise,in0,in1,out = infer_util \
                           .get_data_by_mode(obj['dataset'],1)
  for o,b in zip(out,bias):
    print("out=%s bias=%s" % (o,b))

  infer_vis.plot_bias("bias.png",in0,in1,out,bias)
  infer_vis.plot_noise("noise.png",in0,in1,out,noise)
  bnds_z = infer_fit.infer_model(out_z,in0,in1,out, \
                                  bias,noise,adc=False)

  for o,b in zip(out,bias):
    print("out=%s bias=%s" % (o,b))
  input("ic")

  input("ss")

  print(obj)
