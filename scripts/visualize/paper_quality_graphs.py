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
  def sct(time):
    tsc = xform[0]
    toff = xform[1]
    return (time-toff)/tsc

  def scv(value):
    #vsc = xform[2]
    #voff = xform[3]
    voff = 0.0
    vsc = 1.0
    return (value-voff)/vsc

  thw = list(map(lambda t: sct(t)*tau*glbls.TIME_FREQUENCY, tmeas))
  yhw = list(map(lambda x: scv(x)/scf, ymeas))
  return thw, yhw

def resample(t,x,n):
  stride  = math.floor(len(t)/n)
  assert(len(t) == len(x))
  tr = list(map(lambda i: t[i*stride], range(n)))
  xr = list(map(lambda i: x[i*stride], range(n)))
  return tr,xr

YLABELS = {
  'micro-osc': 'amplitude',
  'vanderpol': 'amplitude',
  'pend': 'position',
  'robot': 'xvel',
  'pend-nl': 'position',
  'lotka': 'population',
  'spring': 'position',
  'cosc': 'amplitude',
  'spring-nl': 'position',
  'heat1d-g2': 'heat',
  'heat1d-g4': 'heat',
  'heat1d-g8': 'heat'

}

def plot_quality(bmark,subset,model,experiments):
  print("%s %s %s %d" % (bmark,subset,model,len(experiments)))

  # compute reference using information from first element
  entry = experiments[0]
  output = list(entry.outputs())[0]
  TREF,YREF = run_reference_simulation(entry.bmark, \
                                       entry.math_env, \
                                       output.varname)
  palette = sns.color_palette()
  ax = plt.subplot(1, 1, 1)
  ax.set_xlabel('simulation time')
  ax.set_ylabel(YLABELS[bmark])
  ax.set_title(common.BenchmarkVisualization.benchmark(bmark))
  #ax.set_grid(False)
  ax.set_xlim((min(TREF),max(TREF)))
  ax.grid(False)
  n_execs = 0
  for exp in experiments:
    for out in exp.outputs():
      n_execs += 1

  alpha = 0.3
  # compute experimental results
  for exp in experiments:
    for out in exp.outputs():
      TMEAS,YMEAS = read_meas_data(output.out_file)
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
      ax.plot(TSCR,YSCR,alpha=0.7,label='measured', \
              color='#5758BB', \
              linestyle='--')

  ax.plot(TREF,YREF,label='reference',linestyle='-', \
          color='#EE5A24')
  plt.tight_layout()
  filename = "paper-%s-%s-%s.pdf" % (subset,bmark,model)
  filepath = common.get_path(filename)
  plt.savefig(filepath)
  plt.clf()

def visualize():
  db = ExperimentDB()
  by_bmark = {}
  for exp in db.get_by_status(ExperimentStatus.RAN):
    if exp.quality is None:
      continue

    key = (exp.bmark,exp.subset,exp.model)
    print(key)
    if not key in by_bmark:
      by_bmark[key] = []

    by_bmark[key].append(exp)


  for (bmark,subset,model),experiments in by_bmark.items():
    plot_quality(bmark,subset,model,experiments)
