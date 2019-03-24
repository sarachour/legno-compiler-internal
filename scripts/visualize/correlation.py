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

def visualize():
  data = common.get_data(series_type='bmark')

  all_ranks = []
  all_qualities = []
  corrs = {}
  for ser in data.series():

    opt,_ident,_rank,_quality,_quality_var = data.get_data(ser, \
                                                   ['objective_fun','ident','rank',\
                                                    'quality','quality_variance'], \
                                                   [MismatchStatus.UNKNOWN, MismatchStatus.IDEAL])
    bad_ident,bad_rank,bad_quality = data.get_data(ser, \
                                                   ['ident','rank', \
                                                    'quality'], \
                                                   [MismatchStatus.BAD])


    '''
    sel_inds = list(filter(lambda i: 'rand' in opt[i] or 'sig-tau0' == opt[i] or \
                           'lnz-tau0' in opt[i], \
                           range(0,len(_rank))))
    '''
    sel_inds = list(range(0,len(_rank)))
    if len(sel_inds) == 0:
      continue
    rank = list(map(lambda i : _rank[i], sel_inds))
    quality= list(map(lambda i : _quality[i], sel_inds))
    ident = list(map(lambda i : _ident[i], sel_inds))
    quality_var= list(map(lambda i : _quality_var[i], sel_inds))
    max_rank = max(rank)
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

    plot_ranks = list(map(lambda r: r/max_rank, rank))
    plt.errorbar(plot_ranks,quality,quality_var,fmt='^',
                 marker='.',label=ser)

    plt.xlabel('rank (norm)')
    plt.ylabel('quality (norm)')
    plt.title('rank vs quality')
    plt.legend()
    plt.savefig("rank_%s.png" % ser)
    plt.clf()


  coeff = np.corrcoef(all_ranks,all_qualities)
  for ser,corr in corrs.items():
    print("%s\t%f" % (ser,corr))

  print("global\t%f" % coeff[1][0])
  print("\n")
  print("[GLOBAL] rank-corr : %s" % (coeff[1][0]))
