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
from bmark.bmarks.common import run_diffeq
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
    TREF,YREF = [],[]
    I = prob.variable_order.index(varname)
    for t,y in zip(*run_diffeq(menv,prob)):
      z = prob.curr_state(menv,t,y)
      TREF.append(t)
      YREF.append(z[I])

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


def fit(_tref,_yref,_tmeas,_ymeas):
  def measure_error(tref,xref,tobs,xobs,model):
    a,b,c,d = model
    thw = a*tref + b
    xhw = c*xref + d
    return thw,xhw

  def compute_error(ht,hx,mt,mx,model):
    rt,rx = measure_error(ht,hx,mt,mx,model)
    if min(rt) < min(mt) or max(rt) > max(mt):
        return 2.0
    y = np.interp(rt, mt, mx, left=0, right=0)
    error = np.sum((y-rx)**2)/len(y)
    return error

  def apply_model_to_obs(ht,mt,mx,model):
    a,b,c,d = model
    tmin,tmax = b, b+max(ht*a)
    inds = list(filter(lambda i: mt[i] <= tmax and mt[i] >= tmin, \
                    range(len(mt))))
    rt = list(map(lambda i: (mt[i]-b)/a,inds))
    rx = list(map(lambda i: mx[i], inds))
    return rt,rx


  tref = np.array(_tref)
  yref = np.array(_yref)
  tmeas = np.array(_tmeas)
  ymeas = np.array(_ymeas)

  def compute_loss(x):
    error = compute_error(tref,yref,tmeas,ymeas, \
                            [x[0],x[1],1.0,0.0])
    return error

 
  bounds = [(1.0, 3.0),(0.0,max(tmeas)*0.15)]
  print("finding transform...")
  a,b = optimize.brute(compute_loss, bounds)
  model = [a,b,1.0,0.0]
  print(model)
  rt,rx = apply_model_to_obs(tref,tmeas,ymeas,model)
  return rt,rx,model

def compute_quality(_tobs,_yobs,_tpred,_ypred):
  tpred = np.array(_tpred)
  ypred = np.array(_ypred)
  tobs = np.array(_tobs)
  yobs = np.array(_yobs)
  ypred_flow = np.interp(tobs, tpred, ypred, left=0, right=0)
  error = math.sqrt(np.median((ypred_flow-yobs)**2))
  print("quality=%s" % error)
  return error

def analyze(entry):
  path_h = paths.PathHandler('default',entry.bmark)
  QUALITIES = []
  print(entry)
  VARS = set(map(lambda o: o.varname, entry.outputs()))
  for output in entry.outputs():
    varname = output.varname
    trial = output.trial
    TREF,YREF = compute_ref(entry.bmark,entry.math_env,varname)
    TMEAS,YMEAS = read_meas_data(output.out_file)
    scf = max(abs(np.array(YMEAS)))/max(abs(np.array(YREF)))
    THW,YHW = scale_ref_data(output.tau,scf,TREF,YREF)
    TFIT,YFIT,MODEL = fit(THW,YHW,TMEAS,YMEAS)

    common.simple_plot(output,path_h,output.trial,'ref',TREF,YREF)
    common.simple_plot(output,path_h,output.trial,'meas',TMEAS,YMEAS)
    common.simple_plot(output,path_h,output.trial,'pred',THW,YHW)
    common.simple_plot(output,path_h,output.trial,'obs',TFIT,YFIT)
    common.compare_plot(output,path_h,output.trial,'comp',THW,YHW,TFIT,YFIT)

    QUALITY = compute_quality(THW,YHW,TFIT,YFIT)

    output.set_transform(MODEL)
    output.set_quality(QUALITY)
    QUALITIES.append(QUALITY)



  QUALITY = np.median(QUALITIES)
  entry.set_quality(QUALITY)
