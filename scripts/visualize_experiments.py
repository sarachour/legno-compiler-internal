from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus, MismatchStatus
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
    if not entry.quality is None:
      get(quality_to_time,entry).append(entry.quality/entry.runtime)
    else:
      get(quality_to_time,entry).append(None)

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
  data = get_data(series_type='bmarks')
  ranks = data['ranks']
  qualities= data['qualities']
  idents = data['idents']
  mismatches = data['mismatches']
  mismatch_threshold=MismatchStatus.NONIDEAL

  for ser in data['series']:
    if len(ranks[ser]) == 0:
      continue

    n = len(ranks[ser])
    inds = list(filter(lambda i: mismatches[ser][i].to_score() > 0.0,range(0,n)))
    good_ranks = list(map(lambda i: ranks[ser][i], inds))
    good_qualities = list(map(lambda i: qualities[ser][i], inds))
    good_idents = list(map(lambda i: idents[ser][i],inds))
    max_rank = max(good_ranks)
    max_quality= max(good_qualities)
    mismatch = list(map(lambda mm : mm.to_score(), mismatches[ser]))

    for r,q,o,m in zip(ranks[ser],qualities[ser],idents[ser],mismatches[ser]):
      mtag = "G" if m.to_score() > 0.0 else "B"
      print("%s [%s]rank=%s, quality=%s" % (mtag, o,r,q))
    coeff = np.corrcoef(good_ranks,good_qualities)
    print("[%s] rank-corr : %s" % (ser,coeff[1][0]))
    if n > len(inds):
      coeff = np.corrcoef(ranks[ser],mismatch)
      print("[%s] mismatch-corr : %s" % (ser,coeff[1][0]))

    plot_ranks = list(map(lambda rank: rank/max_rank, good_ranks))
    plot_qualities = list(map(lambda qual: qual/max_quality, good_qualities))
    plt.scatter(plot_ranks,plot_qualities,label=ser)
    print("\n")

  plt.xlabel('rank')
  plt.ylabel('quality')
  plt.title('rank vs quality')
  plt.legend()
  plt.savefig("rank.png")
  plt.clf()

def summarize_best(key,executed_only=True,mismatch_threshold=MismatchStatus.NONIDEAL):
  data = get_data(executed_only=executed_only)
  values = data[key]
  opts = data['opts']
  circ_idents = data['circ_idents']
  series= data['series']
  mismatches = data['mismatches']
  for ser in series:
    by_ident = {}
    for ident,opt,value,mismatch in zip(circ_idents[ser], \
                               opts[ser], \
                               values[ser], \
                               mismatches[ser]):
      if not ident in by_ident:
        by_ident[ident] = {}

      if mismatch.to_score() > 0.0:
        by_ident[ident][opt] = value

    for ident in by_ident:
      print("%s" % ident)
      labels = list(by_ident[ident].keys())
      vals = list(map(lambda k: by_ident[ident][k],labels))
      indices = np.argsort(vals)
      for i in indices:
        print("   %s: %s" % (labels[i],vals[i]))

def quality_vs_speed():
  key_vs_speed('qualvspeed','qualities')

def rank_vs_speed():
  key_vs_speed('rankvspeed','ranks')


def best_quality_to_speed():
  summarize_best('qualities_to_times')


def best_quality():
  summarize_best('qualities')

def best_speed():
  summarize_best('times')

def best_ranked():
  summarize_best('ranks',executed_only=False)

def strip_tau(opt):
  return opt.split('-tau')[0]

def key_vs_speed(tag,key,log=False):
  data = get_data(series_type='circ_idents')
  qualities = data[key]
  times = data['times']
  series= data['series']
  mismatches= data['mismatches']
  opts = data['opts']
  allowed = ['lo-noise','slow','fast']
  for ser in series:
    n = len(times[ser])
    time,quality,mismatch,opt = times[ser],qualities[ser], \
                                mismatches[ser],opts[ser]

    inds = list(filter(lambda i : mismatch[i].to_score() > 0.0, list(range(0,n))))
    max_quality = max(map(lambda i: quality[i], inds))
    max_time = max(time)

    # noise values
    optset = set(map(lambda i: strip_tau(opts[ser][i]),inds))
    for opt in optset:
      if opt == 'slow' or opt == 'fast' or \
         opt == 'maxsigfast' or opt == 'maxsigslow' or 'tau' in opt:
        continue

      marker = 'x'
      if 'lo-noise' in opt or 'maxsig' == opt:
        marker = '^'

      opt_inds = list(filter(lambda i : opt == strip_tau(opts[ser][i]), inds))
      norm_opt_time = list(map(lambda i: time[i]/max_time, opt_inds))
      if log:
        norm_opt_quality = list(map(lambda i: np.log10(quality[i]), opt_inds))
      else:
        norm_opt_quality = list(map(lambda i: quality[i], opt_inds))
      print("%s/%s : %d" % (ser,opt,len(norm_opt_quality)))
      plt.scatter(norm_opt_time,norm_opt_quality,marker=marker,label=opt)

      plt.xlabel('runtime (norm)')
      plt.ylabel(key)
      plt.title('speed vs %s' % key)

    plt.legend()
    plt.savefig("%s_%s.png" % (tag,ser))
    plt.clf()

def execute(args):
  name = args.type
  opts = {
    'quality-vs-speed':quality_vs_speed,
    'rank-vs-speed':rank_vs_speed,
    'correlation': correlation,
    'best-rank': best_ranked,
    'best-quality': best_quality,
    'best-quality-to-speed': best_quality_to_speed,
    'best-speed': best_speed
  }
  if name in opts:
    opts[name]()
  else:
    for opt in opts.keys():
      print(": %s" % opt)
    raise Exception("unknown routine <%s>" % name)
