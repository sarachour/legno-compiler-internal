import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt


def strip_tau(opt):
  return opt.split('-tau')[0]

def visualize():
  data = common.get_data(series_type='circ_ident')
  fields = ['runtime','rank','objective_fun']
  whitelist = ['sig','nz','lo-noise','maxsig','lo-noise-fast']
  for ser in data.series():
    runtimes,ranks,opts= data.get_data(ser, fields, \
                                       [MismatchStatus.UNKNOWN, \
                                        MismatchStatus.IDEAL])

    max_time = max(runtimes)
    # noise values
    n = len(opts)
    stripopts = list(map(lambda i: strip_tau(opts[i]),range(0,n)))
    for opt in set(stripopts):
      if not opt in whitelist:
        continue
      if opt == 'lnz' or opt == 'sig':
        marker = 'x'
      else:
        marker = 'o'

      opt_inds = list(filter(lambda i : opt == stripopts[i], range(0,n)))
      opt_time = list(map(lambda i: runtimes[i]/max_time, opt_inds))
      opt_rank = list(map(lambda i: ranks[i], opt_inds))

      print("%s/%s : %d" % (ser,opt,len(opt_inds)))
      plt.scatter(opt_time,opt_rank, \
                   marker=marker,label=opt)

      plt.xlabel('runtime (norm)')
      plt.ylabel('rank')
      plt.title('speed vs rank')

    plt.legend()
    plt.savefig("rankvspeed_%s.png" % (ser))
    plt.clf()
