import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import math

def strip_tau(opt):
  return opt.split('-tau')[0]

def opt_order(prefix):
  for idx in range(0,7):
    yield "%s-tau%d" % (prefix,idx)

def by_opt(sel,opt,data):
  inds = list(filter(lambda i: opt[i] == sel, range(0,len(opt))))
  new_data = []
  for datum in data:
    new_datum = list(map(lambda i: datum[i], inds))
    new_data.append(new_datum)
  return new_data

def plot_series(data,colormap,ser):
  fields = ['runtime','quality','objective_fun','quality_variance','bmark']
  colors = sns.color_palette()
  runtimes,qualities,opts,variances,bmarks = data.get_data(ser, fields, \
                                                           [MismatchStatus.UNKNOWN, \
                                                           MismatchStatus.IDEAL])
  bmark = bmarks[0]
  if not bmark in colormap:
    colormap[bmark] = colors[len(colormap.keys())]
    color = colormap[bmark]
    label = bmark
  else:
    color = colormap[bmark]
    label = None

  n = len(opts)
  max_time = max(runtimes)
  speedup = list(map(lambda x : max_time/x, runtimes))
  # plot tradeoff curve
  x = []
  y =[]
  e=[]
  for sel_opt in opt_order('sig'):
    opt_quals,opt_vars, opt_speedup = by_opt(sel_opt,opts, \
                                             [qualities,variances,speedup])
    if not (len(opt_quals) == 1):
      print("skipped: '%s:%s [%d]" % (ser,sel_opt,len(opt_quals)))
      continue

    y.append(opt_quals[0])
    x.append(opt_speedup[0])
    e.append(opt_vars[0])

  plt.errorbar(x,y,e,c=color,label=label)
  opt_quals,opt_vars,opt_speedup = by_opt('lo-noise-fast',opts,[qualities,variances,speedup])
  plt.errorbar(opt_speedup,opt_quals,opt_vars,fmt='^', \
                  marker='o',c=color)

def visualize():
  data = common.get_data(series_type='circ_ident')
  colormap = {}
  for ser in data.series():
    plot_series(data,colormap,ser)

  plt.xlabel('speedup (norm)')
  plt.ylabel('quality (snr)')
  plt.title('quality vs speedup')
  plt.legend()
  plt.savefig("paper_qvs.png")
  plt.clf()
