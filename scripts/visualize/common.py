from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus, MismatchStatus
import numpy as np

class Dataset:

  def __init__(self,key):
    self._key = key
    self._data = {}
    self._fields = ['ident','circ_ident','bmark', \
                    'objective_fun', 'rank', 'mismatch',
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

  def series(self):
    return self._data.keys()

  def add(self,entry):
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
      qualities = list(map(lambda o: o.quality, entry.outputs()))
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
