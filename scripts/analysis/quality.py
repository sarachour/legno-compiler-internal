import numpy as np
from scipy import stats
import tqdm
import math
import time
import json
import util.paths as paths
import bmark.menvs as menvs
from scipy import optimize
import bmark.diffeqs as diffeqs
from bmark.bmarks.common import run_system
import chip.hcdc.globals as glbls
import util.util as util

import scripts.analysis.common as common

CACHE = {}

def scale_ref_data(tau,scf,tref,yref):
  thw = list(map(lambda t: t/tau*1.0/glbls.TIME_FREQUENCY, tref))
  yhw = list(map(lambda x: x*scf, yref))
  return thw, yhw


def compute_ref(bmark,menvname,varname):
  if not (bmark,menvname,varname) in CACHE:
    prob = diffeqs.get_prog(bmark)
    menv = menvs.get_math_env(menvname)
    T,D = run_system(menv,prob)
    TREF,YREF = T,D[varname]

    CACHE[(bmark,menvname,varname)] = (TREF,YREF)
    return TREF,YREF
  else:
      return CACHE[(bmark,menvname,varname)]

def read_meas_data(filename):
  with open(filename,'r') as fh:
    obj = util.decompress_json(fh.read())
    T,V = obj['times'], obj['values']
    T_REFLOW = np.array(T) - min(T)
    print("mean: %s" % np.mean(V))
    return T_REFLOW,V

def make_prediction(t_ref,x_ref,model):
    a,b,c,d = model
    t_pred = a*t_ref + b
    x_pred = c*x_ref + d
    return t_pred,x_pred

def compute_error(ref_t,ref_x,meas_t,meas_x,model):
  res_t,res_x = make_prediction(ref_t,ref_x,model)
  if min(res_t) < min(meas_t) or max(res_t) > max(meas_t):
      return 2.0
  meas_x_reflow = np.interp(res_t, meas_t, meas_x, left=0, right=0)
  error = np.sum((meas_x_reflow-res_x)**2)/len(res_t)
  return error

def apply_model_to_obs(pred_t,meas_t,meas_x,model):
    a,b,c,d = model
    tmin,tmax = b, b+max(pred_t*a)
    inds = list(filter(lambda i: meas_t[i] <= tmax and meas_t[i] >= tmin, \
                    range(len(meas_t))))
    rt = list(map(lambda i: (meas_t[i]-b)/a,inds))
    rx = list(map(lambda i: (meas_x[i]-d)/c, inds))
    return rt,rx

def out_of_bounds(bounds,result):
  for (lb,ub),r in zip(bounds,result):
    if r < lb or r > ub:
      print("%s not in (%s,%s)" % (r,lb,ub))
      continue
      #return True
  return False

def fit(_tref,_yref,_tmeas,_ymeas):
  # apply transform to turn ref -> pred
  tref = np.array(_tref)
  yref = np.array(_yref)
  tmeas = np.array(_tmeas)
  ymeas = np.array(_ymeas)

  def compute_loss(x):
    error = compute_error(tref,yref,tmeas,ymeas, \
                            [x[0],x[1],1.0,0.0])
    return error

  bounds = [
    (0.97,1.13),
    (0.0,max(tmeas)*0.10),
  ]
  print("=== finding transform ===")
  #n = 5
  n = 10
  result = optimize.brute(compute_loss, bounds, Ns=n)
  model = [result[0],result[1],1.0,0.0]
  print(model)
  if out_of_bounds(bounds,result):
    return None,None,model

  infer_t,infer_x = apply_model_to_obs(tref,tmeas,ymeas,model)
  return infer_t,infer_x,model

def apply_model(_tref,_yref,_tmeas,_ymeas,model):
  # apply transform to turn ref -> pred
  tref = np.array(_tref)
  yref = np.array(_yref)
  tmeas = np.array(_tmeas)
  ymeas = np.array(_ymeas)
  print(model)

  infer_t,infer_x = apply_model_to_obs(tref,tmeas,ymeas,model)
  return infer_t,infer_x

def compute_quality(_tobs,_yobs,_tpred,_ypred):
  def compute_error(ypred,yobs):
    return (ypred-yobs)**2

  tpred,ypred = np.array(_tpred), np.array(_ypred)
  tobs,yobs = np.array(_tobs), np.array(_yobs)
  n = len(tobs)
  ypred_flow = np.interp(tobs, tpred, ypred, left=0, right=0)
  errors = np.array(list(map(lambda i: compute_error(ypred_flow[i], \
                                                     yobs[i]), range(n))))

  # SSQE
  if n == 0:
    return -1
  ssqe = math.sqrt(sum(errors)/n)
  print("mean (errors): %s" % ssqe)
  max_val = max(map(lambda v: abs(v), ypred))
  norm_ssqe = ssqe/max_val
  print("norm mean (errors): %s" % norm_ssqe)
  return norm_ssqe,tobs,errors

def analyze(entry,recompute=False,no_reference=False):
  path_h = paths.PathHandler(entry.subset,entry.bmark)
  QUALITIES = []
  print(entry)
  VARS = set(map(lambda o: o.varname, entry.outputs()))
  MODEL = None
  for output in entry.outputs():
    varname = output.varname
    trial = output.trial
    print(output)

    TMEAS,YMEAS = read_meas_data(output.out_file)
    common.simple_plot(output,path_h,output.trial,'meas',TMEAS,YMEAS)

    if no_reference:
      QUALITIES.append(-1)
      continue

    TREF,YREF = compute_ref(entry.bmark,entry.math_env,varname)
    common.simple_plot(output,path_h,output.trial,'ref',TREF,YREF)

    TPRED,YPRED = scale_ref_data(output.tau,output.scf,TREF,YREF)
    common.simple_plot(output,path_h,output.trial,'pred',TPRED,YPRED)

    if not output.model is None:
      MODEL = output.transform

    if MODEL is None or recompute:
      TFIT,YFIT,MODEL = fit(TPRED,YPRED,TMEAS,YMEAS)
    else:
      TFIT,YFIT = apply_model(TPRED,YPRED,TMEAS,YMEAS,MODEL)
    output.set_transform(MODEL)

    if TFIT is None or YFIT is None:
      QUALITIES.append(-1)
      continue

    common.simple_plot(output,path_h,output.trial,'obs',TFIT,YFIT)
    common.compare_plot(output,path_h,output.trial,'comp',TPRED,YPRED,TFIT,YFIT)
    RESULT = compute_quality(TFIT,YFIT,TPRED,YPRED)
    if RESULT == -1:
      QUALITIES.append(RESULT)
      continue

    QUALITY,TERR,YERR = RESULT
    common.simple_plot(output,path_h,output.trial,'err',TERR,YERR)
    output.set_quality(QUALITY)
    QUALITIES.append(QUALITY)


  if len(QUALITIES) > 0:
    QUALITY = np.median(QUALITIES)
    entry.set_quality(QUALITY)
