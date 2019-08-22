import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
import compiler.infer_pass.infer_fit as infer_fit

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
                  handle=':z[0]')
  out_zp = PortModel('integrator',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode, \
                  handle=':z\'')
  out_z = PortModel('integrator',loc,'out', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode, \
                  handle=':z')

  ic = PortModel('integrator',loc,'ic', \
                  comp_mode=comp_mode, \
                  scale_mode=scale_mode)
  return scale_mode,inp,ic,out,out_z,out_z0,out_zp


def infer(obj):
  scm,model_in,model_ic,model_out, \
    out_z,out_z0,out_zp = build_config(obj['metadata'])

  insc,outsc = scm
  scale = outsc.coeff()/insc.coeff()
  bnds_ic = infer_fit.build_model(out_z0,obj['dataset'],0, \
                                  0.04)


  cl_bias,cl_var,_,_,cl_zero = infer_util \
                     .get_data_by_mode(obj['dataset'],1)

  tc_error,tc_R2,_,_,tc = infer_util \
                     .get_data_by_mode(obj['dataset'],2)

  ol_bias,ol_R2,_,_,ol_zero = infer_util \
                     .get_data_by_mode(obj['dataset'],3)

  out_z.gain = (tc+tc_error)/tc;
  out_z.bias = ol_bias;
  print("tau=%f confidence=%f" % (out_z.gain, tc_R2))

  if infer_util.about_one(out_z.gain):
    out_z.gain = 1.0

  if infer_util.about_one(out_z0.gain):
    out_z0.gain = 1.0

  yield model_in
  yield model_ic
  yield model_out
 
