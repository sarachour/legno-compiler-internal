from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import bmark.diffeqs as diffeqs
from bmark.bmarks.common import run_system
import chip.hcdc.globals as glbls
import bmark.menvs as menvs
import util.util as util
import scripts.visualize.common as common
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import math

def run_reference_simulation(bmark,menvname,varname):
  prob = diffeqs.get_prog(bmark)
  menv = menvs.get_math_env(menvname)
  T,D = run_system(menv,prob)
  TREF,YREF = T,D[varname]
  return TREF,YREF

def read_meas_data(filename):
  with open(filename,'r') as fh:
    obj = util.decompress_json(fh.read())
    T,V = obj['times'], obj['values']
    T_REFLOW = np.array(T) - min(T)
    return T_REFLOW,V

def scale_measured_data(xform,tau,scf,tmeas,ymeas):
  tc = tau*glbls.TIME_FREQUENCY
  def sct(time):
    tsc = xform[0]
    toff = xform[1]
    return (time-toff)*tc/tsc

  def scv(value,scf):
    #vsc = xform[2]
    #voff = xform[3]
    voff = 0.0
    vsc = 1.0
    return (value-voff)/(scf*vsc)

  thw = list(map(lambda t: sct(t), tmeas))
  yhw = list(map(lambda x: scv(x,scf), ymeas))
  return thw, yhw

def resample(t,x,n):
  stride  = math.floor(len(t)/n)
  assert(len(t) == len(x))
  tr = list(map(lambda i: t[i*stride], range(n)))
  xr = list(map(lambda i: x[i*stride], range(n)))
  return tr,xr

YLABELS = {
  'micro-osc': 'amplitude',
  'micro-osc-with-gain': 'amplitude',
  'vanderpol': 'amplitude',
  'pend': 'position',
  'closed-forced-vanderpol': 'amplitude',
  'robot': 'xvel',
  'pend-nl': 'position',
  'lotka': 'population',
  'spring': 'position',
  'cosc': 'amplitude',
  'kalman-const': 'constant',
  'spring-nl': 'position',
  'heat1d-g2': 'heat',
  'heat1d-g4': 'heat',
  'heat1d-g4-wg': 'heat',
  'heat1d-g8': 'heat',
  'heat1d-g8-wg': 'heat',
  'gentoggle':'conc',
  'bont':'conc',
  'smmrxn':'conc',
  'epor':'conc',
  'kalman-const':'state'
}

def plot_preamble(entry,TREF,YREF):
 # compute reference using information from first element
  output = list(entry.outputs())[0]
  palette = sns.color_palette()
  ax = plt.subplot(1, 1, 1)
  title = common.BenchmarkVisualization.benchmark(entry.bmark)
  ax.set_xlabel('simulation time',fontsize=18)
  ax.set_ylabel(YLABELS[entry.bmark],fontsize=18)
  ax.set_xticklabels([])
  ax.set_yticklabels([])
  ax.set_title(title,fontsize=20)
  #ax.set_grid(False)
  ax.set_xlim((min(TREF),max(TREF)))
  ax.grid(False)

  ax.plot(TREF,YREF,label='reference',
          linestyle='-', \
          linewidth=4, \
          color='#EE5A24')
  return ax

def plot_quality(identifier,experiments):

  print(identifier)
  def plot_waveform(out,alpha):
    TMEAS,YMEAS = read_meas_data(out.out_file)
    xform = out.transform
    tau = out.tau
    scf = out.scf
    TSC,YSC = scale_measured_data(out.transform,
                                  out.tau,
                                  out.scf,
                                  TMEAS,
                                  YMEAS
    )
    TSCR,YSCR = resample(TSC,YSC,len(TREF))
    ax.plot(TSCR,YSCR,alpha=alpha,
            label='measured', \
            color='#5758BB', \
            linewidth=4.0, \
            linestyle='--')

  # compute reference using information from first element
  entry = experiments[0]
  output = list(entry.outputs())[0]
  TREF,YREF = run_reference_simulation(entry.bmark, \
                                       entry.math_env, \
                                       output.varname)
  ax = plot_preamble(entry,TREF,YREF)
  n_execs = 0
  for exp in experiments:
    for out in exp.outputs():
      n_execs += 1

  outputs = []
  # compute experimental results
  for exp in experiments:
    for out in exp.outputs():
      outputs.append(out)
      # the subsequent runs have issues with the fit.
      plot_waveform(out,0.6/n_execs+0.4)

  plt.tight_layout()
  filename = "paper-%s-all.pdf" % (identifier)
  filepath = common.get_path(filename)
  plt.savefig(filepath)
  plt.clf()

  ax = plot_preamble(entry,TREF,YREF)
  valid_outputs = list(filter(lambda o: not o.quality is None, outputs))

  if len(valid_outputs) == 0:
    plt.clf()
    return

  best_output = min( \
    valid_outputs, \
    key=lambda o: o.quality)
  plot_waveform(best_output,1.0)
  plt.tight_layout()
  filename = "paper-%s-best.pdf" % (identifier)
  filepath = common.get_path(filename)
  plt.savefig(filepath)
  plt.clf()

def to_identifier(exp):
  mode,_,_,bw = util.unpack_tag(exp.model)
  inds = "x".join(map(lambda i: str(i), exp.arco_indices))
  key = "%s-%s-%s-%s" % (exp.bmark,exp.subset,inds,mode)
  return key

def visualize():
  db = ExperimentDB()
  by_bmark = {}
  for exp in db.get_by_status(ExperimentStatus.RAN):
    if exp.quality is None:
      continue

    key = to_identifier(exp)
    if not key in by_bmark:
      by_bmark[key] = []

    by_bmark[key].append(exp)


  for identifier,experiments in by_bmark.items():
    plot_quality(identifier,experiments)
