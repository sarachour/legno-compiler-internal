from bmark.bmarks.common import run_system

from scripts.common import ExecutionStatus
from scripts.expdriver_db import ExpDriverDB
import scripts.analysis.quality as quality_analysis

import util.util as util
import scripts.visualize.common as common
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import math

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
  'heat1d-g9': 'heat',
  'heat1d-g8-wg': 'heat',
  'gentoggle':'conc',
  'bont':'conc',
  'smmrxn':'conc',
  'epor':'conc',
  'kalman-const':'state',
  'kalman-freq-small':'state'
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
  ax.set_xlim((min(TREF),max(TREF)))
  margin = (max(YREF)-min(YREF))*0.1
  lb= min(YREF)-margin
  ub = max(YREF)+margin
  ax.set_ylim((lb,ub))
  ax.grid(False)

  ax.plot(TREF,YREF,label='reference',
          linestyle='-', \
          linewidth=4, \
          color='#EE5A24')
  return ax

def plot_quality(identifier,experiments):

  print(identifier)
  def plot_waveform(out,alpha):
    TMEAS,YMEAS = quality_analysis.read_meas_data(out.out_file)
    print(out.transform)
    TREC,YREC = quality_analysis.scale_obs_data(out,TMEAS,YMEAS)
    print(min(TREC),max(TREC))
    ax.plot(TREC,YREC,alpha=alpha,
            label='measured', \
            color='#5758BB', \
            linewidth=4.0, \
            linestyle='--')

    if 'standard' in identifier:
      clb,cub = ax.get_ylim()
      margin = (max(YREC)-min(YREC))*0.1
      lb= min(YREC)-margin
      ub = max(YREC)+margin
      ax.set_ylim(min(lb,clb),max(ub,cub))

  # compute reference using information from first element
  entry = experiments[0]
  output = list(entry.outputs())[0]
  TREF,YREF = quality_analysis.compute_ref(entry.bmark, \
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

def visualize(db):
  by_bmark = {}
  for exp in db.experiment_tbl \
               .get_by_status(ExecutionStatus.RAN):
    if exp.quality is None:
      continue

    key = to_identifier(exp)
    if not key in by_bmark:
      by_bmark[key] = []


    by_bmark[key].append(exp)

  for identifier,experiments in by_bmark.items():
    plot_quality(identifier,experiments)
