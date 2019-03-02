import os
import time
import json
import matplotlib.pyplot as plt
import numpy as np
import tqdm
import math

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
def compute_running_snr(T,Y,nmax=100000):
  n_segs = 100
  win_size = int(len(T)/float(n_segs))
  MEAN,STDEV,SNR,TIME = [],[],[],[]
  win_low = 0
  win_hi = win_size
  n = len(Y)
  step = int(round(n/nmax)) if nmax < n else 1
  for i in tqdm.tqdm(range(0,n,step)):
    if win_hi - win_low + 1 < win_size:
      continue
    u = np.array(Y[win_low:win_hi+1])
    t = np.array(T[win_low:win_hi+1])
    mean = np.mean(u)
    stdev = np.std(u)
    MEAN.append(mean)
    STDEV.append(stdev)
    SNR.append(abs(mean)/stdev)
    TIME.append(np.mean(t))
    win_low += 1
    if win_hi < n-1:
      win_hi += 1

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
  bw = cfg.bandwidth(port)
  tc = (conc_circ.board.time_constant)*(conc_circ.tau)
  pnlib.compute(conc_circ)
  snr = skelter.snr(conc_circ,block_name,loc,port)
  return snr,bw.bandwidth,tc,scf


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
    RANK,FMAX,TC,SCF = compute_params(conc_circ,varname)
    output.set_rank(RANK)

  RANK = skelter.rank(conc_circ)
  entry.set_rank(RANK)

def truncate_signal(t,y):
  nsegs = 40
  pts = np.linspace(min(t),max(t),nsegs)
  bounds = []
  means = []
  stds = []
  for i in range(1,nsegs):
    lb,ub = pts[i-1],pts[i]
    inds = list(filter(lambda i: t[i]<=ub and t[i]>=lb, \
                       range(0,len(t))))
    mean = np.mean(list(map(lambda i: y[i], inds)))
    std = np.std(list(map(lambda i: y[i], inds)))
    means.append(mean)
    stds.append(std)
    bounds.append((lb,ub))

  trim_front = 0
  stop = False
  for i in range(0,nsegs-1):
    if stds[i] < 0.025 and not stop:
      trim_front = i
    else:
      stop=True

  trim_back= 0
  stop = False
  for i in range(nsegs-2,0,-1):
    if stds[i] < 0.025 and not stop:
      trim_back = i
    else:
      stop=True

  time_low,_ = bounds[trim_front]
  _,time_hi = bounds[trim_back]
  inds = list(filter(lambda i: t[i]<=time_hi and t[i]>=time_low, \
                       range(0,len(t))))
  t_cut = list(map(lambda i: t[i], inds))
  y_cut = list(map(lambda i: y[i], inds))
  return t_cut,y_cut

def analyze_quality(entry,conc_circ):
  path_h = paths.PathHandler('default',entry.bmark)
  QUALITIES = []
  for output in entry.outputs():
    varname = output.varname
    TREF,YREF = compute_ref(entry.math_env,varname,entry.bmark)
    TMEAS,YMEAS = compute_meas(output.out_file)
    simple_plot(output,path_h,'ref',TREF,YREF)
    simple_plot(output,path_h,'meas',TMEAS,YMEAS)

    _,FMAX,TC,SCF = compute_params(conc_circ,varname)
    TMEAS_CUT, YMEAS_CUT = truncate_signal(TMEAS,YMEAS)
    simple_plot(output,path_h,'cut',TMEAS_CUT,YMEAS_CUT)
    TIME,MEAN,STDEV,SNR = \
          compute_running_snr(TMEAS_CUT,YMEAS_CUT)

    simple_plot(output,path_h,'snr',TIME,SNR)
    mean_std_plot(output,path_h,'dist',TIME,MEAN,STDEV)
    QUALITY= np.mean(SNR)
    output.set_quality(QUALITY)

    QUALITIES += SNR

  AGG_QUALITY = np.mean(QUALITIES)
  entry.set_quality(AGG_QUALITY)

def execute(args):
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
