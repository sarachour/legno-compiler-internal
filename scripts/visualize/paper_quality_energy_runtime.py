import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import math
import util.util as util

def visualize():
  statuses = [MismatchStatus.UNKNOWN, \
             MismatchStatus.IDEAL]
  data = common.get_data(series_type='bmark')
  desc = "performance, energy and quality for HDACv2 Board"
  table = common.Table("Results", desc, "tblres", \
                       layout = "|c|c|ccc|")
  table.two_column = False
  header = [
          'bandwidth', \
          'runtime', \
          'power', \
          'energy' \
  ]
  table.set_fields(header)
  table.horiz_rule();
  table.header()
  table.horiz_rule();
  for ser in common.Plot.benchmarks():
    if data.has_series(ser):
      fields = ['runtime','energy','quality','quality_variance','model']
      result = data.get_data(ser,fields,statuses)
      print(result)
      runtime,energy,quality,quality_variance,model = result
      row = {}
      method,ana_error,dig_error,bandwidth= util.unpack_tag(model[0])
      row['runtime'] = "%.2f ms" % (runtime[0]*1e3)
      row['power'] = "%.2f $\mu$W" % (energy[0]*1e6)
      row['energy'] = "%.2f $\mu$J" % (energy[0]*runtime[0]*1e6)
      #row['ssqe'] = "%.4f $\pm$ %.4f" \
      #                 % (quality[0],quality_variance[0])
      #row['minimum digital snr'] = "%f" % dig_error
      #row['minimum analog snr'] = "%f" % ana_error
      row['bandwidth'] = "%dkhz" % int(bandwidth/1000)

      table.data(ser,row)
  table.horiz_rule();
  table.write(common.get_path('quality-energy-runtime.tbl'))
