import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt


def strip_tau(opt):
  if '-tau' in opt:
    return opt.split('-tau')[0]
  elif 'rand' in opt:
    return 'rand'
  else:
    return opt

def visualize():
  data = common.get_data(series_type='circ_ident')
  fields = ['runtime','quality','objective_fun','quality_variance']
  whitelist = ['sig','lnz','lo-noise','maxsigfast','rand', \
               'lo-noise-fast','maxsigslow','heur']
  for ser in data.series():
    runtimes,qualities,opts,variances = data.get_data(ser, fields, \
                                   [MismatchStatus.UNKNOWN, \
                                    MismatchStatus.IDEAL])

    max_time = max(runtimes)
    # noise values
    n = len(opts)
    stripopts = list(map(lambda i: strip_tau(opts[i]),range(0,n)))
    for opt in set(stripopts):
      if not opt in whitelist:
        continue
      if opt == 'lnz' or opt == 'sig' or opt == 'rand':
        marker = 'x'
      else:
        marker = 'o'

      opt_inds = list(filter(lambda i : opt == stripopts[i], range(0,n)))
      opt_time = list(map(lambda i: runtimes[i]/max_time, opt_inds))
      opt_quality = list(map(lambda i: qualities[i], opt_inds))
      opt_variance = list(map(lambda i: variances[i], opt_inds))

      print("%s/%s : %d" % (ser,opt,len(opt_inds)))
      plt.errorbar(opt_time,opt_quality,opt_variance,fmt='^', \
                   marker=marker,label=opt)

      plt.xlabel('runtime (norm)')
      plt.ylabel('quality')
      plt.title('speed vs quality')

    plt.legend()
    plt.savefig("qualvspeed_%s.png" % (ser))
    plt.clf()
