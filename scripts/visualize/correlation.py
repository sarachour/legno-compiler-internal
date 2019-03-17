import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt

def visualize():
  data = common.get_data(series_type='bmark')

  for ser in data.series():

    ident,rank,quality,quality_var = data.get_data(ser, \
                                                   ['ident','rank','quality','quality_variance'], \
                                                   [MismatchStatus.UNKNOWN, MismatchStatus.IDEAL])
    bad_ident,bad_rank,bad_quality = data.get_data(ser, \
                                                   ['ident','rank','quality'], \
                                                   [MismatchStatus.BAD])


    max_rank = max(rank)
    max_quality= max(quality)

    for r,q,o in zip(bad_rank,bad_quality,bad_ident):
      print("B [%s]rank=%s, quality=%s" % (o,r,q))


    for r,q,o in zip(rank,quality,ident):
      print("G [%s]rank=%s, quality=%s" % (o,r,q))

    randomize_ranks = []
    randomize_qualities = []
    samples = 10
    for r,q,v in zip(rank,quality,quality_var):
      for _ in range(0,samples):
        qrand = np.random.normal(q,v)
        randomize_ranks.append(r)
        randomize_qualities.append(qrand)

    if len(rank) < 2:
      print("[%s] rank-corr: <need more data>" % ser)

    else:
      coeff = np.corrcoef(randomize_ranks,randomize_qualities)
      print("[%s] rank-corr : %s" % (ser,coeff[1][0]))

    print("\n")

    plot_ranks = list(map(lambda r: r/max_rank, rank))
    plot_qualities = list(map(lambda q: q, quality))
    plot_variances = list(map(lambda q: q, quality_var))
    plt.errorbar(plot_ranks,plot_qualities,plot_variances,fmt='^',
                 marker='.',label=ser)

    plt.xlabel('rank (norm)')
    plt.ylabel('quality (norm)')
    plt.title('rank vs quality')
    plt.legend()
    plt.savefig("rank_%s.png" % ser)
    plt.clf()
