from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus, MismatchStatus
import numpy as np
from enum import Enum
import seaborn as sns
import util.util as util

def get_path(filename):
  path = "PAPER/%s" % filename
  util.mkdir_if_dne("PAPER")
  return path

def unpack_model(handle):
  method = "unknown"
  i=0
  if handle[i] == 'n':
    method="naive"
  elif handle[i] == 'i':
    method="ideal"
  elif handle[i] == 'x':
    method="physics"

  i += 1
  assert(handle[i] == 'q')
  i += 1
  analog = float(handle[i:i+4])
  i += 4
  assert(handle[i] == 'd')
  i += 1
  digital= float(handle[i:i+4])
  i += 4
  assert(handle[i] == 'b')
  return method,analog,digital

class Dataset:

  def __init__(self,key):
    self._key = key
    self._data = {}
    self._fields = ['ident','circ_ident','bmark', \
                    'objective_fun', 'model',\
                    'rank', 'mismatch',
                    'jaunt_circ_file',
                    'quality','runtime','energy']
    self._metafields = ['quality_variance','quality_time_ratio']

  def get_data(self,series,fields,statuses):
    data = dict(map(lambda f: (f,[]), fields))
    for status in statuses:
      if not status in self._data[series]:
        continue

      for field in fields:
        data[field] += self._data[series][status][field]

    ord_data = []
    for field in fields:
      ord_data.append(data[field])
    return ord_data

  def has_series(self,ser):
    return ser in self._data

  def series(self):
    return self._data.keys()

  def add(self,entry):
    if not isinstance(self._key, str):
      raise Exception("not string: %s" % self._key)

    key = getattr(entry,self._key)
    if not key in self._data:
      self._data[key] = {}

    if not entry.mismatch in self._data[key]:
      self._data[key][entry.mismatch] = {}
      for field in self._fields + self._metafields:
        self._data[key][entry.mismatch][field] = []

    for field in self._fields:
      value = getattr(entry,field)
      self._data[key][entry.mismatch][field].append(value)

    if entry.quality is None:
      self._data[key][entry.mismatch]['quality_variance'] \
          .append(0)
      self._data[key][entry.mismatch]['quality_time_ratio'] \
          .append(0)

    else:
      qualities = list(filter(lambda q: not q is None, \
                              map(lambda o: o.quality, entry.outputs())))
      self._data[key][entry.mismatch]['quality_variance'] \
          .append(np.std(qualities))

      quality_to_time = entry.quality/entry.runtime
      self._data[key][entry.mismatch]['quality_time_ratio'] \
        .append(quality_to_time)

def get_data(series_type='bmarks',executed_only=True):
  db = ExperimentDB()
  data = Dataset(series_type)

  for entry in db.get_all():
    if executed_only and \
       (entry.quality is None or entry.runtime is None):
      continue

    data.add(entry)

  return data

class BenchmarkVisualization:
  BENCHMARK_ORDER = ['micro-osc',
                     'cosc',
                     'pend',
                     'pend-nl',
                     'spring',
                     'spring-nl',
                     'vanderpol',
                     'robot',
                     'heat1d-g2',
                     'heat1d-g4',
                     'heat1d-g8'
  ]
  BENCHMARK_NAMES = {
    'micro-osc': 'sin',
    'cosc': 'dampened',
    'vanderpol': 'vanderpol',
    'pend': 'pendulum',
    'pend-nl': 'pendulum-nl',
    'lotka': 'lotka-volterra',
    'spring': 'springs',
    'spring-nl': 'springs-nl',
    'robot': 'robot',
    'heat1d-g2': 'heat2-1',
    'heat1d-g4': 'heat4-2',
    'heat1d-g6': 'heat6-3',
    'heat1d-g8': 'heat8-4',
  }

  @staticmethod
  def benchmark(runname):
    return BenchmarkVisualization.BENCHMARK_NAMES[runname]

  @staticmethod
  def benchmarks():
    return BenchmarkVisualization.BENCHMARK_ORDER


class Plot(BenchmarkVisualization):

  MARKERS = ['x','^',',','_','v','+','|','D','s']*2
  COLORS = list(sns.color_palette())*2

  MARKER_MAP = {}
  COLOR_MAP = {}
  for i,bmark in \
      enumerate(BenchmarkVisualization.BENCHMARK_ORDER):
    MARKER_MAP[bmark] = MARKERS[i]
    COLOR_MAP[bmark] = COLORS[i]

  def __init__(self):
    BenchmarkVisualization.__init__(self)

  @staticmethod
  def get_color(bmark):
    return Plot.COLOR_MAP[bmark]

  @staticmethod
  def get_marker(bmark):
    return Plot.MARKER_MAP[bmark]


class Table(BenchmarkVisualization):

  class LineType(Enum):
    HRULE = "hrule"
    HEADER = "header"
    DATA = "data"

  def __init__(self,name,description, \
               handle,layout, \
               loc='tp', \
               benchmarks=True):
    BenchmarkVisualization.__init__(self)
    self._name = name
    self._handle = handle
    self._layout = layout
    self._loc = loc
    self._benchmarks = benchmarks
    self._description = description
    self.lines = []

 
  def horiz_rule(self):
    self.lines.append((Table.LineType.HRULE,None))

  def header(self):
    self.lines.append((Table.LineType.HEADER,None))

  def data(self,bmark,fields):
    if self._benchmarks:
      paper_bmark = Table.BENCHMARK_NAMES[bmark]
      assert(not 'benchmark' in fields)
      fields['benchmark'] = paper_bmark
    self.lines.append((Table.LineType.DATA,fields))

  @property
  def fields(self):
    return self._fields

  def set_fields(self,header):
    if self._benchmarks:
      self._fields = ['benchmark'] + header
    else:
      self._fields = header

  def to_table(self):
    lines = []
    hdr = self._fields
    q = lambda l: lines.append(l)
    q('table')
    q(self._loc)
    q(self._description)
    q('tbl:%s' % self._handle)
    q(self._layout)
    for typ,line in self.lines:
      if typ == Table.LineType.HRULE:
        q('HLINE')
      elif typ == Table.LineType.HEADER:
        headerstr = ",".join(hdr)
        q(headerstr)
      elif typ == Table.LineType.DATA:
        els = []
        for h in hdr:
          if h in hdr:
            els.append(str(line[h]))
          else:
            els.append("")
        datastr = ",".join(els)
        q(datastr)

    return "\n".join(lines)

  def write(self,filename):
    with open(filename,'w') as fh:
      fh.write(self.to_table())
