import numpy as np
from scipy import stats
import math
import time
import json
import util.paths as paths
from scipy import optimize
import util.util as util
import matplotlib.pyplot as plt
from scipy import signal, fftpack
import scripts.analysis.common as common

CACHE = {}

def scale_obs_data(output,tobs,yobs):
  transform = output.transform
  time_scale = 1.0/(transform.legno_time_scale \
                    *transform.time_constant)
  exp_time_scale = transform.expd_time_scale
  exp_time_offset = transform.expd_time_offset
  val_scale = transform.legno_ampl_scale
  trec = list(map(lambda t: (t-exp_time_offset)/(time_scale*exp_time_scale), \
                  tobs))
  yrec = list(map(lambda x: x/val_scale, yobs))
  tmin = 0
  tmax = output.runtime/time_scale
  inds = list(filter(lambda i: trec[i] <= tmax and trec[i] >= tmin, \
                     range(len(trec))))
  trec_trim = util.array_map(map(lambda i: trec[i],inds))
  yrec_trim = util.array_map(map(lambda i: yrec[i],inds))
  return trec_trim, yrec_trim


def scale_ref_data(output,tref,yref):
  transform = output.transform
  time_scale = 1.0/(transform.legno_time_scale \
                    *transform.time_constant)
  time_offset = 0.0
  val_scale = transform.legno_ampl_scale
  print(time_scale,time_offset)
  thw = list(map(lambda t: t*time_scale+time_offset, tref))
  yhw = list(map(lambda x: x*val_scale, yref))
  return thw, yhw


def compute_ref(bmark,menvname,varname):
  import bmark.menvs as menvs
  import bmark.diffeqs as diffeqs
  from bmark.bmarks.common import run_system

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


def lag_finder(t1,y1,t2,y2):
  n = 10000
  times = np.linspace(min(t1),max(t1),n)
  dt = np.mean(np.diff(times))
  y2_reflow= np.interp(times,t2,y2,left=0,right=0)
  y1_reflow= np.interp(times,t1,y1,left=0,right=0)
  corr = signal.correlate(y1_reflow,y2_reflow)
  offset = np.argmax(corr)
  t_delta = (offset-n)*dt
  return -t_delta

def fit(output,_tref,_yref,_tmeas,_ymeas):
  def out_of_bounds(bounds,result):
    new_result = []
    assert(len(bounds) == len(result))
    for (lb,ub),r in zip(bounds,result):
      if r < lb or r > ub:
        print("%s not in (%s,%s)" % (r,lb,ub))
      new_result.append(max(min(r,ub),lb))

    assert(len(new_result) == len(result))
    return new_result

  def apply_model_to_obs(pred_t,meas_t,meas_x,model):
    a,b,c,d = model
    tmin,tmax = b, b+max(pred_t*a)
    inds = list(filter(lambda i: \
                       meas_t[i] <= tmax \
                       and meas_t[i] >= tmin, \
                       range(len(meas_t))))
    rt = list(map(lambda i: (meas_t[i]-b)/a,inds))
    rx = list(map(lambda i: (meas_x[i]-d)/c, inds))
    return rt,rx

  # apply transform to turn ref -> pred
  tref = np.array(_tref)
  yref = np.array(_yref)
  tmeas = np.array(_tmeas)
  ymeas = np.array(_ymeas)

  t_delta = lag_finder(tref,yref,tmeas,ymeas)
  xform = output.transform
  xform.expd_time_offset = t_delta
  # update database
  output.transform = xform

def compute_quality(output,_trec,_yrec,_tref,_yref):
  def compute_error(ypred,yobs):
    return (ypred-yobs)**2

  tref,yref= np.array(_tref), np.array(_yref)
  trec,yrec= np.array(_trec), np.array(_yrec)
  plt.plot(trec,yrec)
  plt.plot(tref,yref)
  plt.savefig("debug.png")
  plt.clf()
  n = len(tref)
  yobs_flow = np.interp(tref, trec, yrec, left=0, right=0)
  errors = np.array(list(map(lambda i: compute_error(yobs_flow[i], \
                                                     yref[i]), range(n))))

  score = sum(errors)
  print("SCORE: %s" % score)
  return score,tref,errors

def analyze(entry,recompute=False,no_reference=False):
  path_h = paths.PathHandler(entry.subset,entry.bmark)
  QUALITIES = []
  VARS = set(map(lambda o: o.varname, entry.outputs()))
  MODEL = None
  for output in entry.outputs():
    varname = output.varname
    trial = output.trial

    TMEAS,YMEAS = read_meas_data(output.out_file)
    common.simple_plot(output,path_h,output.trial,'meas',TMEAS,YMEAS)
    if no_reference:
      QUALITIES.append(-1)
      continue

    #if not output.quality is None:
    #  QUALITIES.append(output.quality)

    TREF,YREF = compute_ref(entry.bmark,entry.math_env,varname)
    common.simple_plot(output,path_h,output.trial,'ref',TREF,YREF)

    TPRED,YPRED = scale_ref_data(output,TREF,YREF)
    common.simple_plot(output,path_h,output.trial,'pred',TPRED,YPRED)

    fit(output,TPRED,YPRED,TMEAS,YMEAS)
    TFIT,YFIT = scale_obs_data(output,TMEAS,YMEAS)

    if TFIT is None or YFIT is None:
      QUALITIES.append(-1)
      continue

    common.simple_plot(output,path_h,output.trial,'rec',TFIT,YFIT)
    common.compare_plot(output,path_h,output.trial,'comp',TREF,YREF,TFIT,YFIT)
    RESULT = compute_quality(output,TFIT,YFIT,TREF,YREF)
    if RESULT == -1:
      QUALITIES.append(RESULT)
      continue

    QUALITY,TERR,YERR = RESULT
    common.simple_plot(output,path_h,output.trial,'err',TERR,YERR)
    output.quality = QUALITY
    QUALITIES.append(QUALITY)


  if len(QUALITIES) > 0:
    QUALITY = np.median(QUALITIES)
    entry.set_quality(QUALITY)
