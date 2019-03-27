import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt
from chip.conc import ConcCirc
from chip.hcdc.hcdcv2_4 import board as hdacv2_board
from enum import Enum

def to_table(summary):
  to_header = {
    'tile_out': 'crossbar',
    'tile_in': 'crossbar',
    'ext_chip_out': 'crossbar',
    'ext_chip_in': 'crossbar',
    'tile_dac':'dac',
    'tile_adc':'adc',
    'lut':'lut',
    'fanout': 'fanout',
    'multiplier': 'multiplier',
    'integrator': 'integrator',
    'conns': 'connections'
  }
  table = common.Table('Circuit Configurations', 'circcfg','c|ccccccc|c')
  table.set_fields(['integrator','multiplier', \
                    'fanout','adc','dac','lut', \
                    'crossbar','connections'])
  table.horiz_rule()
  table.header()
  for bmark in table.benchmarks:
    data = summary[bmark]
    fields = dict(map(lambda f: (f,0), table.fields))
    for key,value in data['blocks'].items():
      fields[to_header[key]] += value

    fields[to_header['conns']] += data['conns']
    table.data(bmark,fields)

  table.horiz_rule()
  table.write('compcount.tbl')

def visualize():
  data = common.get_data(series_type='circ_ident')
  summary = {}
  for ser in data.series():
    conc_circ_files,bmarks = data.get_data(ser, ['jaunt_circ_file','bmark'], \
                                    [MismatchStatus.UNKNOWN,
                                     MismatchStatus.IDEAL])
    conc_circ = conc_circ_files[0]
    bmark = bmarks[0]
    if bmark in summary:
      continue

    summary[bmark] = {
      'conns': 0,
      'blocks': {}
    }

    conc_circ = ConcCirc.read(hdacv2_board,conc_circ)
    for block_name,loc,_ in conc_circ.instances():
      if not block_name in summary[bmark]['blocks']:
        summary[bmark]['blocks'][block_name] = 0
      summary[bmark]['blocks'][block_name] += 1

    summary[bmark]['conns']= len(list(conc_circ.conns()))

  to_table(summary)
