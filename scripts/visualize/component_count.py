import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt
from chip.conc import ConcCirc
from enum import Enum
from chip.hcdc.hcdcv2_4 import make_board

#board = make_board('standard')

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
  desc = 'analog chip configuration statistics'
  table = common.Table('Circuit Configurations',desc, 'circcfg','|c|ccccccc|c|')
  table.set_fields(['blocks','integrator','multiplier', \
                    'fanout','adc','dac','lut', \
                    'crossbar','connections'])
  table.horiz_rule()
  table.header()
  table.horiz_rule()
  for bmark in table.benchmarks():
    fields = dict(map(lambda f: (f,0), table.fields))
    if not bmark in summary:
      continue

    data = summary[bmark]
    for key,value in data['blocks'].items():
      fields[to_header[key]] += value

    fields[to_header['conns']] += data['conns']
    fields['blocks'] = data['blocks']
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
      'total': 0,
      'blocks': {}
    }

    conc_circ = ConcCirc.read(board,conc_circ)
    for block_name,loc,_ in conc_circ.instances():
      if not block_name in summary[bmark]['blocks']:
        summary[bmark]['blocks'][block_name] = 0
      summary[bmark]['blocks'][block_name] += 1
      summary[bmark]['total'] += 1

    summary[bmark]['conns']= len(list(conc_circ.conns()))

  to_table(summary)
