import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import seaborn as sns
sns.set()
import matplotlib.pyplot as plt
import math

def strip_tau(opt):
  if '-tau' in opt:
    return opt.split('-tau')[0]
  elif 'rand' in opt:
    return 'rand'
  else:
    return opt

def plot_bmark(data,ax,ser):
  fields = ['runtime','quality','quality_variance','bmark']
  runtimes,qualities,variances,bmarks = data.get_data(ser, fields, \
                                                           [MismatchStatus.UNKNOWN, \
                                                            MismatchStatus.IDEAL])
  bmark = bmarks[0]

  runtime_ms= list(map(lambda x : x*1000, runtimes))
  ax.scatter(runtime_ms,qualities,
             c=common.Plot.get_color(bmark), \
             label=common.Plot.benchmark(bmark),
             marker=common.Plot.get_marker(bmark))

def visualize():
  data = common.get_data(series_type='bmark')
  colormap = {}
  markermap = {}
  sns.set_style("whitegrid")
  f, ax = plt.subplots()
  for ser in common.Plot.benchmarks():
    if data.has_series(ser):
      plot_bmark(data,ax,ser)

  ax.axhline(5, linestyle='dashed', alpha=0.5)
  ax.text(x=4.0, y=7, s='minimum SNR', alpha=0.7, color='#334f8d')
  ax.set_xlabel('Runtime (ms)')
  ax.set_ylabel('Quality (SNR)')
  ax.set_title('SNR to Speedup')
  ax.legend(loc=9,ncol=4,\
             bbox_to_anchor=(0.5, -0.15))
  plt.savefig("paper-qvr.pdf", bbox_inches='tight')
  plt.clf()
