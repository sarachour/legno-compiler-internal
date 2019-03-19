import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt

import chip.units as units

def strip_tau(opt):
  return opt.split('-tau')[0]

def visualize():
  data = common.get_data(series_type='circ_ident')
  fields = ['energy','quality','objective_fun','quality_variance']
  whitelist = ['sig','lnz','lo-noise','maxsig','lo-noise-fast','maxsigslow']
  for ser in data.series():
    energies,qualities,opts,variances = data.get_data(ser, fields, \
                                   [MismatchStatus.UNKNOWN, \
                                    MismatchStatus.IDEAL])

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
      opt_energy= list(map(lambda i: energies[i]/units.uJ, opt_inds))
      opt_quality = list(map(lambda i: qualities[i], opt_inds))
      opt_variance = list(map(lambda i: variances[i], opt_inds))

      print("%s/%s : %d" % (ser,opt,len(opt_inds)))
      plt.errorbar(opt_energy,opt_quality,opt_variance,fmt='^', \
                   marker=marker,label=opt)

      plt.xlabel('energy (uJ)')
      plt.ylabel('quality')
      plt.title('energy vs quality')

    plt.legend()
    plt.savefig("envspeed_%s.png" % (ser))
    plt.clf()
