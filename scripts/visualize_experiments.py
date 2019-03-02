from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import matplotlib.pyplot as plt
import numpy as np
import math

def get_data(series_type='bmarks',executed_only=True):
  db = ExperimentDB()
  qualities = {}
  ranks = {}
  times = {}
  mismatches = {}
  bmarks = {}
  opts = {}
  idents = {}

  def get(dict_,entry):
    if series_type == 'bmarks':
      ser = entry.bmark
    elif series_type == 'opts':
      ser = entry.objective_fun
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
    get(bmarks,entry).append(entry.bmark)
    get(opts,entry).append(entry.objective_fun)
    get(ranks,entry).append(entry.rank)
    get(mismatches,entry).append(entry.mismatch)
    get(qualities,entry).append(entry.quality)
    get(times,entry).append(entry.runtime)

  return {
    'series':bmarks.keys(),
    'idents':idents,
    'bmarks':bmarks,
    'opts':opts,
    'ranks':ranks,
    'qualities':qualities,
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

def best_quality():
  series,idents,_,opts,_,qualities,_ = get_data()
  for bmark,qualvals in qualities.items():
    if len(qualvals) == 0:
      continue
    idx = np.argmax(qualvals)
    best_opt = opts[bmark][idx]
    print("[%s] %s / %s" % (bmark,best_opt,qualvals[idx]))
    for o,v in zip(idents[bmark],qualvals):
      print("   %s: %s" % (o,v))

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
  elif name == 'best-quality':
    best_quality()
  else:
    raise Exception("unknown")
