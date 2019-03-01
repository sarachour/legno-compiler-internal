from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import matplotlib.pyplot as plt
import numpy as np
import math

def get_data(series_type='bmarks',executed_only=True):
  db = ExperimentDB()
  bmarks = ['micro-osc-quarter','micro-osc-quad','micro-osc-one', \
            'spring','vanderpol','pend','cosc']
  opts = ['fast','slow','max','maxstab']
  if series_type == 'bmarks':
    series = bmarks
  elif series_type == 'opts':
    series = opts
  else:
    raise Exception("unknown")

  qualities = dict(map(lambda opt: (opt,[]), series))
  ranks = dict(map(lambda opt: (opt,[]), series))
  times = dict(map(lambda opt: (opt,[]), series))
  bmark_fields = dict(map(lambda opt: (opt,[]), series))
  opt_fields = dict(map(lambda opt: (opt,[]), series))

  for entry in db.get_all():
    if not entry.bmark in bmarks:
      continue

    if executed_only and \
       (entry.quality is None or entry.runtime is None):
      continue

    if not entry.rank is None:
      if series_type == 'bmarks':
        ser = entry.bmark
      elif series_type == 'opts':
        ser=  entry.objective_fun

      bmark_fields[ser].append(entry.bmark)
      opt_fields[ser].append(entry.objective_fun)
      ranks[ser].append(entry.rank)
      qualities[ser].append(entry.quality)
      times[ser].append(entry.runtime)

  return series,bmark_fields,opt_fields,ranks,qualities,times


def correlation():
  series,_,_,ranks,qualities,_ = get_data()
  for ser in series:
    if len(ranks[ser]) == 0:
      continue

    coeff = np.corrcoef(ranks[ser],qualities[ser])
    print("[%s] correlation:\n%s\n" % (ser,coeff))
    plt.scatter(ranks[ser],qualities[ser],label=ser)

  plt.legend()
  plt.savefig("rank.png")
  plt.clf()

def best_ranked():
  series,_,opts,ranks,_,_ = get_data(executed_only=False)
  for bmark,rankvals in ranks.items():
    if len(rankvals) == 0:
      continue
    idx = np.argmax(rankvals)
    best_opt = opts[bmark][idx]
    print("[%s] %s / %s" % (bmark,best_opt,rankvals[idx]))
    for o,v in zip(opts[bmark],rankvals):
      print("   %s: %s" % (o,v))
def rank_vs_quality():
  series,_,_,_,qualities,times = get_data()
  for ser in series:
    plt.scatter(times[ser], qualities[ser],label=ser,s=1.0)

  plt.legend()
  plt.savefig("runt.png")
  plt.clf()

def execute(args):
  name = args.type
  if name == 'rank-vs-quality':
    rank_vs_quality()
  elif name == 'correlation':
    correlation()
  elif name == 'best-ranked':
    best_ranked()
  else:
    raise Exception("unknown")
