from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import matplotlib.pyplot as plt
import numpy as np
import math

def get_data():
  db = ExperimentDB()
  bmarks = ['micro-osc-quarter','micro-osc-quad','micro-osc-one', \
            'spring','vanderpol','pend','cosc']
  opts = ['fast','slow','max','maxstab']
  series = bmarks
  qualities = dict(map(lambda opt: (opt,[]), series))
  ranks = dict(map(lambda opt: (opt,[]), series))
  times = dict(map(lambda opt: (opt,[]), series))
  best_quality = dict(map(lambda opt: (opt,{}), bmarks))
  for entry in db.get_all():
    if not entry.bmark in bmarks:
      continue

  if not entry.quality is None and \
     not entry.runtime is None and \
     not entry.rank is None:
    bmark = entry.bmark
    opt = entry.objective_fun
    ser = bmark
    ranks[ser].append(entry.rank)
    qualities[ser].append(entry.quality)
    times[ser].append(math.log(entry.runtime))

  return ranks,qualities,times


def correlation():
  ranks,qualities,_ = get_data()
  for ser in series:
    coeff = np.corrcoef(ranks[ser],qualities[ser])
    print("[%s] correlation:\n%s\n" % (ser,coeff))
    plt.scatter(ranks[ser],qualities[ser],label=ser)

  plt.legend()
  plt.savefig("rank.png")
  plt.clf()

def rank_vs_quality():
  _,qualities,times = get_data()
  for ser in series:
    plt.scatter(times[ser], qualities[ser],label=ser,s=1.0)

  plt.legend()
  plt.savefig("runt.png")
  plt.clf()
