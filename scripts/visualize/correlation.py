import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt

def compute():
  data = common.get_data(series_type='bmark')
  fields = ['objective_fun','rank','quality']
  corrs = {}
  all_ranks = []
  all_qualities = []
  for ser in data.series():
    opt,rank,quality = \
                  data.get_data(ser, \
                                fields, \
                                [MismatchStatus.UNKNOWN, \
                                 MismatchStatus.IDEAL])
    coeff = np.corrcoef(rank,quality)
    corrs[ser] = coeff[1][0]
    all_ranks += rank
    all_qualities += quality

  coeff = np.corrcoef(all_ranks,all_qualities)
  corrs['global'] = coeff[1][0]
  return corrs

def strip_tau(opt):
  if '-tau' in opt:
    return opt.split('-tau')[0]
  elif 'rand' in opt:
    return 'rand'
  else:
    return opt

def visualize():
  data = common.get_data(series_type='bmark')

  all_ranks = []
  all_qualities = []
  corrs = {}
  color_by_circ = {}
  opt_by_marker = {}

  for ser in data.series():

    _opt,_ident,_rank,_quality,_quality_var,_circ_ident = data.get_data(ser, \
                                                   ['objective_fun','ident','rank',\
                                                    'quality','quality_variance',
                                                   'circ_ident'], \
                                                   [MismatchStatus.UNKNOWN, MismatchStatus.IDEAL])
    bad_ident,bad_rank,bad_quality = data.get_data(ser, \
                                                   ['ident','rank', \
                                                    'quality'], \
                                                   [MismatchStatus.BAD])


    sel_inds = list(filter(lambda i: 'micro-osc-quarter' in _ident[i], \
                           range(0,len(_rank))))
    sel_inds = list(range(0,len(_rank)))
    if len(sel_inds) == 0:
      continue
    rank = list(map(lambda i : _rank[i], sel_inds))
    opt = list(map(lambda i : _opt[i], sel_inds))
    quality= list(map(lambda i : _quality[i], sel_inds))
    ident = list(map(lambda i : _ident[i], sel_inds))
    circ_ident = list(map(lambda i : _circ_ident[i], sel_inds))
    quality_var= list(map(lambda i : _quality_var[i], sel_inds))
    max_rank = (max(rank)-min(rank))+0.1
    min_rank = min(rank)-0.1
    max_quality= max(quality)

    for r,q,o in zip(bad_rank,bad_quality,bad_ident):
      print("B [%s]rank=%s, quality=%s" % (o,r,q))


    for r,q,v,o in zip(rank,quality,quality_var,ident):
      print("G [%s]rank=%s, quality=%s variance=%s" % (o,r,q,v))


    if len(rank) < 2:
      print("[%s] rank-corr: <need more data>" % ser)
      corrs[ser] = None
    else:
      coeff = np.corrcoef(rank,quality)
      all_ranks += rank
      all_qualities += quality
      print("[%s] rank-corr : %s" % (ser,coeff[1][0]))
      corrs[ser] = coeff[1][0]

    print("\n")

    for sid in set(map(lambda o: strip_tau(o), opt)):
    #for sid in set(map(lambda c: c, circ_ident)):
      inds = list(filter(lambda i:strip_tau(opt[i]) == sid, range(0,len(quality))))
      #inds = list(filter(lambda i:circ_ident[i] == sid, range(0,len(quality))))
      ser_rank = list(map(lambda i: (rank[i]-min_rank)/max_rank, inds))
      ser_quality = list(map(lambda i: quality[i], inds))
      ser_variance = list(map(lambda i: quality_var[i], inds))
      plt.errorbar(ser_rank,ser_quality,ser_variance,fmt='^',
                   marker='.',label=sid)

    plt.xlim(0,1.1)
    plt.xlabel('rank (norm)')
    plt.ylabel('quality (norm)')
    plt.title('rank vs quality')
    plt.legend()
    plt.savefig("rank_%s.png" % ser)
    plt.clf()


  coeff = np.corrcoef(all_ranks,all_qualities)
  for ser,corr in corrs.items():
    if corr is None:
      continue
    print("%s\t%f" % (ser,corr))

  print("global\t%f" % coeff[1][0])
  print("\n")
  print("[GLOBAL] rank-corr : %s" % (coeff[1][0]))
