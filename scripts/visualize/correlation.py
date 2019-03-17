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

    max_rank = max(rank)
    max_quality= max(quality)

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

    coeff = np.corrcoef(randomize_ranks,randomize_qualities)
    print("[%s] rank-corr : %s" % (ser,coeff[1][0]))
    print("\n")

    plot_ranks = list(map(lambda r: r/max_rank, randomize_ranks))
    plot_qualities = list(map(lambda q: q, randomize_qualities))
    plt.scatter(plot_ranks,plot_qualities,label=ser)

    plt.xlabel('rank (norm)')
    plt.ylabel('quality (norm)')
    plt.title('rank vs quality')
    plt.legend()
    plt.savefig("rank_%s.png" % ser)
    plt.clf()
