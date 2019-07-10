import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import math


def visualize():
  statuses = [MismatchStatus.UNKNOWN, \
             MismatchStatus.IDEAL]
  data = common.get_data(series_type='bmark')
  desc = "performance, energy and quality for HDACv2 Board"
  table = common.Table("Results", desc, "tblres", \
                       layout = "c|cc|ccc")
  header = ['runtime','power','energy','ssqe']
  table.set_fields(header)
  table.horiz_rule();
  table.header()
  table.horiz_rule();
  for ser in common.Plot.benchmarks():
    if data.has_series(ser):
      fields = ['runtime','energy','quality','quality_variance','model']
      result = data.get_data(ser,fields,statuses)
      runtime,energy,quality,quality_variance,model = result
      row = {}
      method,ana_error,dig_error = common.unpack_model(model[0])
      row['runtime'] = "%.2f ms" % (runtime[0]*1e3)
      row['power'] = "%.2f $\mu$W/s" % (energy[0]*1e6)
      row['energy'] = "%.2f $\mu$W" % (energy[0]*runtime[0]*1e6)
      row['ssqe'] = "%.4f $\pm$ %.4f" \
                       % (quality[0],quality_variance[0])
      row['digital error'] = "%f" % dig_error
      row['analog error'] = "%f" % ana_error

      table.data(ser,row)
  table.horiz_rule();
  table.write(common.get_path('quality-energy-runtime.tbl'))
