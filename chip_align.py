import sys
import util.paths as paths
import bmark.diffeqs as diffeqs
import bmark.menvs as menvs
from bmark.bmarks.common import run_diffeq
from chip.hcdc.hcdcv2_4 import board as hdacv2_board
from chip.conc import ConcCirc
import matplotlib.pyplot as plt
import json
import lab_bench.analysis.waveform as wavelib
import lab_bench.analysis.freq as freqlib
import numpy as np
import math

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

def compute_meas(conc_circ,varname,tmax,filename):
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
  tau = (conc_circ.board.time_constant)*(conc_circ.tau)
  print("scf=%s" % scf)
  print("tau=%s" % conc_circ.tau)
  print("tc=%s" % tau)
  #scf,tau = 1.0,1.0
  #scf = 1.0
  #tau = 1.0
  with open(filename,'r') as fh:
    obj = json.loads(fh.read())
    TMEAS = list(map(lambda t: t*tau, obj['times']))
    YMEAS = list(map(lambda v: v/scf, obj['values']))

  return TMEAS,YMEAS

filename = sys.argv[1]
parts = filename.split('/')
bmarkdir = parts[2]
bmark = parts[3]

path_h = paths.PathHandler(bmarkdir,bmark)
bmark,inds,scale_idx,opt,menvname,hwenv,varname = \
            path_h.measured_waveform_file_to_args(parts[-1])

TREF,YREF = compute_ref(menvname,varname,bmark)
TMAX = max(TREF)

conc_circ_file = path_h.conc_circ_file(bmark,inds,scale_idx,opt)
conc_circ = ConcCirc.read(hdacv2_board, conc_circ_file)

TMEAS,YMEAS = compute_meas(conc_circ,varname,TMAX,filename)
#tsmeas.trim(0,TMAX)
window = 1000
MEAN = []
STDEV = []
SNR = []
for i in range(0,len(YMEAS)):
  win_lo = int(max(i-window/2,0))
  win_hi = int(min(i+window/2,len(YMEAS)-1))
  n = win_hi-win_lo
  ys = YMEAS[win_lo:win_hi+1]
  mean = np.mean(ys)
  stdev = np.std(ys)
  MEAN.append(mean)
  STDEV.append(stdev)
  SNR.append(mean/stdev)

UPPER = list(map(lambda a: a[0]+3.0*a[1],zip(MEAN,STDEV)))
LOWER = list(map(lambda a: a[0]-3.0*a[1],zip(MEAN,STDEV)))
#plt.plot(TMEAS,YMEAS,label='data')
plt.plot(TMEAS,UPPER,label='upper')
plt.plot(TMEAS,LOWER,label='lower')
plt.plot(TMEAS,MEAN,label='mean')
plt.legend()
plt.savefig('analyze')
plt.clf()

plt.plot(TMEAS,STDEV,label='snr')
plt.savefig('snr')

avgsnr = np.mean(SNR)
print("average-snr: %s"% avgsnr)
