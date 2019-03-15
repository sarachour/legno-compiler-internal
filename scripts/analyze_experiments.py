import os
import time
import json
import matplotlib.pyplot as plt
import numpy as np
import tqdm
import math
import time

from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import lab_bench.lib.command as cmd
import lab_bench.lib.expcmd.micro_getter as microget
import lab_bench.lib.expcmd.osc as osc
from chip.conc import ConcCirc
from chip.hcdc.hcdcv2_4 import board as hdacv2_board
import compiler.skelter as skelter
import compiler.common.prop_noise as pnlib
import bmark.diffeqs as diffeqs
import bmark.menvs as menvs
from bmark.bmarks.common import run_diffeq
import util.paths as paths

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

def compute_ref(menvname,varname,bmark):
  prob = diffeqs.get_prog(bmark)
  menv = menvs.get_math_env(menvname)
  TREF,YREF = [],[]
  I = prob.variable_order.index(varname)
  for t,y in zip(*run_diffeq(menv,prob)):
    z = prob.curr_state(menv,t,y)
    TREF.append(t)
    YREF.append(z[I])

  return TREF,YREF


def compute_runtime(conc_circ,menv):
  menv = menvs.get_math_env(menv)
  simtime = menv.sim_time
  tau = (conc_circ.board.time_constant)*(conc_circ.tau)
  hwtime = simtime/tau
  return hwtime


def compute_meas(filename):
  with open(filename,'r') as fh:
    obj = json.loads(fh.read())
    return obj['times'], obj['values']

def compute_params(conc_circ,varname):
  LOC = None
  for block_name,loc,config in conc_circ.instances():
    handle = conc_circ.board.handle_by_inst(block_name,loc)
    if handle is None:
      continue

    for port,label,label_kind in config.labels():
      if label == varname:
        LOC = (block_name,loc,port)

  block_name,loc,port = LOC
  cfg = conc_circ.config(block_name,loc)
  scf = cfg.scf(port)
  tau = (conc_circ.tau)
  pnlib.compute(conc_circ)
  snr = skelter.snr(conc_circ,block_name,loc,port)
  return snr,tau,scf


def mean_std_plot(entry,path_h,tag,t,mean,std):

  UPPER = list(map(lambda a: a[0]+a[1],zip(mean,std)))
  LOWER = list(map(lambda a: a[0]-a[1],zip(mean,std)))
  plt.plot(t,UPPER,label='+std',color='red')
  plt.plot(t,LOWER,label='-std',color='red')
  plt.plot(t,mean,label='mean',color='black')
  plt.legend()
  filename = path_h.plot(entry.bmark,
                         entry.arco_indices,
                         entry.jaunt_index,
                         entry.objective_fun,
                         entry.math_env,
                         entry.hw_env,
                         '%s-%s' % (entry.varname,tag))
  plt.savefig(filename)
  plt.clf()


def simple_plot(entry,path_h,tag,t,x):
  plt.plot(t,x,label=tag)
  plt.legend()
  filename = path_h.plot(entry.bmark,
                         entry.arco_indices,
                         entry.jaunt_index,
                         entry.objective_fun,
                         entry.math_env,
                         entry.hw_env,
                         '%s-%s' % (entry.varname,tag))
  plt.savefig(filename)
  plt.clf()

def analyze_rank(entry,conc_circ):
  for output in entry.outputs():
    varname = output.varname
    RANK,_,_= compute_params(conc_circ,varname)
    output.set_rank(RANK)

  RANK = skelter.rank(conc_circ)
  entry.set_rank(RANK)

def demean_signal(y):
  bias = np.mean(y)
  return list(map(lambda yi: yi-bias,y))

def truncate_signal(t,y,runtime):
  print(max(t),min(t),runtime)
  ttrunc = min(t)+runtime*0.8
  idx = (np.abs(np.array(t)- ttrunc)).argmin()
  return t[0:idx],y[0:idx]

def analyze_quality(entry,conc_circ):
  path_h = paths.PathHandler('default',entry.bmark)
  QUALITIES = []
  VARS = set(map(lambda o: o.varname, entry.outputs()))
  for var in VARS:
    TREF,YREF = compute_ref(entry.math_env,var,entry.bmark)

  for output in entry.outputs():
    varname = output.varname
    TMEAS,YMEAS = compute_meas(output.out_file)
    simple_plot(output,path_h,'ref',TREF,YREF)
    simple_plot(output,path_h,'meas',TMEAS,YMEAS)

    RUNTIME = compute_runtime(conc_circ,entry.math_env)
    TMEAS_CUT, YMEAS_CUT = truncate_signal(TMEAS,YMEAS,RUNTIME)
    YMEAS_ZERO = demean_signal(YMEAS_CUT)
    simple_plot(output,path_h,'cut',TMEAS_CUT,YMEAS_ZERO)
    TIME,MEAN,STDEV,SNR = \
          compute_running_snr(TMEAS_CUT,YMEAS_CUT)

    simple_plot(output,path_h,'snr',TIME,SNR)
    mean_std_plot(output,path_h,'dist',TIME,MEAN,STDEV)
    QUALITY= np.median(SNR)
    print("[[ Quality: %s ]]" % QUALITY)
    output.set_quality(QUALITY)
    QUALITIES += SNR

  AGG_QUALITY = np.mean(QUALITIES)
  print("[[ Agg-Quality: %s ]]" % AGG_QUALITY)
  entry.set_quality(AGG_QUALITY)

def execute_once(args):
  recompute_rank = args.recompute_rank
  recompute_runtime = args.recompute_runtime
  recompute_quality = args.recompute_quality
  recompute_any = recompute_rank or  \
                  recompute_quality or \
                  recompute_runtime

  db = ExperimentDB()
  for entry in db.get_by_status(ExperimentStatus.PENDING):
    if not entry.rank is None and not recompute_rank:
      continue

    print(entry)
    conc_circ = ConcCirc.read(hdacv2_board,entry.skelt_circ_file)
    analyze_rank(entry,conc_circ)

  for entry in db.get_by_status(ExperimentStatus.RAN):
    if not entry.runtime is None \
      and not entry.quality is None \
      and not entry.rank is None \
      and not recompute_any:
      continue

    print(entry)
    conc_circ = ConcCirc.read(hdacv2_board,entry.skelt_circ_file)

    if entry.runtime is None or recompute_runtime:
      runtime = compute_runtime(conc_circ,entry.math_env)
      entry.set_runtime(runtime)

    if entry.rank is None or recompute_rank:
      analyze_rank(entry,conc_circ)

    if entry.quality is None or recompute_quality:
      analyze_quality(entry,conc_circ)

def execute(args):
  daemon = args.monitor
  if not daemon:
    execute_once(args)
  else:
    while True:
      execute_once(args)
      print("...")
      time.sleep(10)
