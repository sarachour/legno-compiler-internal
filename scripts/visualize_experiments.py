from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import matplotlib.pyplot as plt
import numpy as np
import math

def get_data(series_type='bmarks',executed_only=True):
  db = ExperimentDB()
  qualities = {}
  quality_to_time = {}
  ranks = {}
  times = {}
  mismatches = {}
  bmarks = {}
  opts = {}
  idents = {}
  circ_idents= {}

  def get(dict_,entry):
    if series_type == 'bmarks':
      ser = entry.bmark
    elif series_type == 'opts':
      ser = entry.objective_fun
    elif series_type == 'circ_idents':
      ser = entry.circ_ident
    else:
      raise Exception("unknown <%s>" % series_type)

    if not ser in dict_:
      dict_[ser] = []
    return dict_[ser]

  for entry in db.get_all():
    if executed_only and \
       (entry.quality is None or entry.runtime is None):
      continue

    get(idents,entry).append(entry.ident)
    get(circ_idents,entry).append(entry.circ_ident)
    get(bmarks,entry).append(entry.bmark)
    get(opts,entry).append(entry.objective_fun)
    get(ranks,entry).append(entry.rank)
    get(mismatches,entry).append(entry.mismatch)
    get(qualities,entry).append(entry.quality)
    get(times,entry).append(entry.runtime)
    get(quality_to_time,entry).append(entry.quality/entry.runtime)

  return {
    'series':bmarks.keys(),
    'idents':idents,
    'circ_idents':circ_idents,
    'bmarks':bmarks,
    'opts':opts,
    'ranks':ranks,
    'qualities':qualities,
    'qualities_to_times':quality_to_time,
    'mismatches':mismatches,
    'times':times
  }


def correlation():
  data = get_data()
  ranks = data['ranks']
  qualities= data['qualities']
  idents = data['idents']
  mismatches = data['mismatches']

  for ser in data['series']:
    if len(ranks[ser]) == 0:
      continue

    n = len(ranks[ser])
    inds = list(filter(lambda i: not mismatches[ser][i],range(0,n)))
    good_ranks = list(map(lambda i: ranks[ser][i], inds))
    good_qualities = list(map(lambda i: qualities[ser][i], inds))
    good_idents = list(map(lambda i: idents[ser][i],inds))


    for r,q,o in zip(good_ranks,good_qualities,good_idents):
      print("[%s]rank=%s, quality=%s" % (o,r,q))
    coeff = np.corrcoef(good_ranks,good_qualities)
    print("[%s] rank-corr : %s" % (ser,coeff[1][0]))
    if n > len(inds):
      coeff = np.corrcoef(ranks[ser],mismatches[ser])
      print("[%s] mismatch-corr : %s" % (ser,coeff[1][0]))

    plt.scatter(good_ranks,good_qualities,label=ser)

  plt.legend()
  plt.savefig("rank.png")
  plt.clf()

def summarize_best(key,executed_only=True):
  data = get_data(executed_only=executed_only)
  values = data[key]
  opts = data['opts']
  circ_idents = data['circ_idents']
  series= data['series']

  for ser in series:
    by_ident = {}
    for ident,opt,value in zip(circ_idents[ser],opts[ser],values[ser]):
      if not ident in by_ident:
        by_ident[ident] = {}
      by_ident[ident][opt] = value

    for ident in by_ident:
      print("%s" % ident)
      labels = list(by_ident[ident].keys())
      values = list(map(lambda k: by_ident[ident][k],labels))
      indices = np.argsort(values)
      for i in indices:
        print("   %s: %s" % (labels[i],values[i]))

def best_quality_to_runtime():
  summarize_best('qualities_to_times')


def best_quality():
  summarize_best('qualities')

def best_speed():
  summarize_best('times')

def best_ranked():
  summarize_best('ranks',executed_only=False)

def quality_vs_time():
  data = get_data(series_type='circ_idents')
  qualities = data['qualities']
  times = data['times']
  series= data['series']
  for ser in series:
    min_time = min(times[ser])
    min_qual = min(qualities[ser])
    norm_time = list(map(lambda t: t/min_time, times[ser]))
    norm_quality = list(map(lambda q: q/min_qual, qualities[ser]))
    plt.scatter(norm_time,norm_quality)

  plt.savefig("runt.png")
  plt.clf()

def execute(args):
  name = args.type
  opts = {
    'quality-vs-runtime':quality_vs_time,
    'correlation': correlation,
    'best-rank': best_ranked,
    'best-quality': best_quality,
    'best-quality-to-runtime': best_quality_to_runtime,
    'best-speed': best_speed
  }
  if name in opts:
    opts[name]()
  else:
    for opt in opts.keys():
      print(": %s" % opt)
    raise Exception("unknown routine <%s>" % name)
