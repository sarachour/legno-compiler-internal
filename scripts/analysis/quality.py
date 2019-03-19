import numpy as np
from scipy import stats
import tqdm
import math
import time
import json
import util.paths as paths
import bmark.menvs as menvs

import bmark.diffeqs as diffeqs
from bmark.bmarks.common import run_diffeq
import util.util as util

import scripts.analysis.common as common

CACHE = {}
def demean_signal(y):
  bias = np.mean(y)
  return list(map(lambda yi: yi-bias,y))

def truncate_signal(t,y,pred_runtime):
  min_runtime = 0.5*(max(t)-min(t))
  runtime = max(min_runtime,pred_runtime)
  ttrunc = min(t)+runtime
  idx = (np.abs(np.array(t)- ttrunc)).argmin()
  return t[0:idx],y[0:idx]

def apply_linear_noise_model(mean,stdev,yref):
  slope,intercept,_,_,stderr = stats.linregress(mean,stdev)
  print("err: %s" % stderr)
  print("model: %s*v+%s" % (slope,intercept))
  nzref = list(map(lambda y: (y*slope + intercept).real, yref))
  snrref = list(map(lambda args: abs(args[0])/args[1], zip(yref,nzref)))
  return nzref,snrref


def scale_ref_data(entry,tref,yref):
  fmax = entry.fmax
  scf = entry.scf
  thw = list(map(lambda t: t/entry.tau, tref))
  yhw = list(map(lambda x: x*entry.scf*0.5, yref))
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

# FMAX: the maximum frequency in the transformed simulation
def compute_running_snr(T,Y,nmax=10000):
  time_between_pts = np.mean(np.diff(T))
  HWFREQ = 1.0/time_between_pts
  # maximum frequency of chip
  SAMPFREQ = 400000*2.0
  win_size = int(HWFREQ/SAMPFREQ)
  MEAN,STDEV,SNR,TIME = [],[],[],[]
  n = len(Y)
  step = int(round(n/nmax)) if nmax < n else 1

  print(" n: %s" % n)
  print(" hw_freq: %s" % HWFREQ)
  print(" mt_freq: %s" % SAMPFREQ)
  print(" step: %s" % step)
  print(" win: %s" % win_size)
  for i in tqdm.tqdm(range(0,n,step)):
    win_hi = min(round(i+win_size/2.0),n-1)
    win_lo = max(round(i-win_size/2.0),0)
    if win_hi - win_lo < win_size/6.0:
      continue

    u = np.array(Y[win_lo:win_hi+1])
    t = np.array(T[win_lo:win_hi+1])
    mean = np.mean(u)
    stdev = np.std(u)
    MEAN.append(mean)
    STDEV.append(stdev)
    SNR.append(abs(mean)/stdev)
    TIME.append(np.mean(t))

  return TIME,MEAN,STDEV,SNR

def read_meas_data(filename):
  with open(filename,'r') as fh:
    obj = util.decompress_json(fh.read())
    T,V = obj['times'], obj['values']
    T_REFLOW = np.array(T) + min(T)
    return T_REFLOW,V

def analyze(entry):
  path_h = paths.PathHandler('default',entry.bmark)
  QUALITIES = []
  VARS = set(map(lambda o: o.varname, entry.outputs()))
  for output in entry.outputs():
    varname = output.varname
    trial = output.trial
    TREF,YREF = compute_ref(entry.bmark,entry.math_env,varname)
    THW,YHW = scale_ref_data(output,TREF,YREF)

    TMEAS,YMEAS = read_meas_data(output.out_file)

    common.simple_plot(output,path_h,output.trial,'ref',TREF,YREF)
    common.simple_plot(output,path_h,output.trial,'meas',TMEAS,YMEAS)

    RUNTIME = entry.runtime
    TMEAS_CUT, YMEAS_CUT = truncate_signal(TMEAS,YMEAS,RUNTIME)
    YMEAS_ZERO = demean_signal(YMEAS_CUT)
    common.simple_plot(output,path_h,output.trial,'cut',TMEAS_CUT,YMEAS_ZERO)
    TIME,MEAN,STDEV,_ = \
          compute_running_snr(TMEAS_CUT,YMEAS_CUT)

    NZHW, SNRHW = apply_linear_noise_model(MEAN,STDEV,YHW)
    QUALITY= np.median(SNRHW)
    common.mean_std_plot(output,path_h,output.trial,'dist',TREF,YHW,NZHW)
    common.simple_plot(output,path_h,output.trial,'snr',THW,SNRHW)
    print("[[ SNR Quality: %s ]]" % QUALITY)
    QUALITIES.append(QUALITY)

    output.set_quality(QUALITY)


  QUALITY = np.median(QUALITIES)
  entry.set_quality(QUALITY)
