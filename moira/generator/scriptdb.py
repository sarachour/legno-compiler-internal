import tinydb as tdb
import os
from enum import Enum
import json

class MoiraScriptPathHandler:

  def __init__(self):
    self.set_root_dir()
    if not os.path.exists(self.ROOT_DIR):
      os.makedirs(self.ROOT_DIR)
    if not os.path.exists(self.TIME_DIR):
      os.makedirs(self.TIME_DIR)
    if not os.path.exists(self.FREQ_DIR):
      os.makedirs(self.FREQ_DIR)
    if not os.path.exists(self.SCRIPT_DIR):
      os.makedirs(self.SCRIPT_DIR)
    if not os.path.exists(self.PLOT_DIR):
      os.makedirs(self.PLOT_DIR)
    if not os.path.exists(self.MODEL_DIR):
      os.makedirs(self.MODEL_DIR)


  def set_root_dir(self):
    self.ROOT_DIR = "output/moira"
    self.SCRIPT_DIR = self.ROOT_DIR + "/scripts"
    self.TIME_DIR = self.ROOT_DIR + "/time"
    self.FREQ_DIR = self.ROOT_DIR + "/freq"
    self.PLOT_DIR = self.ROOT_DIR + "/plot"
    self.MODEL_DIR = self.ROOT_DIR + "/model"


  def script_file(self,ident):
    return self.SCRIPT_DIR+ "/%s.grendel" % (ident)

  def timeseries_file(self,ident):
    return self.TIME_DIR+ "/%s.json" % (ident)

  def database_file(self,name):
    return self.ROOT_DIR+"/%s.json" % name

  def has_file(self,filename):
    return os.path.exists(filename)

class MoiraScriptEntry:

  def __init__(self,name,inputs,consts,output):
    self._name = name
    self._inputs = inputs
    self._consts = consts
    self._pointers = {}
    self._reference = None
    self._output = output

  @property
  def name(self):
    return self._name

  @property
  def output(self):
    return self._output

  def add_pointer(self,varname,ptr_entry):
    assert(isinstance(ptr_entry,MoiraScriptEntry))
    self._pointers[varname] = ptr_entry

  def pointers(self):
    for varname,ptr in self._pointers.items():
      yield varname,ptr

  def set_reference(self,ref):
    self._reference = ref

  def identifier(self):
    def to_list(d):
      for k1,datum in d.items():
        for k2,value in d[k1].items():
          yield (k1,k2),value

    ident = "%s_" % self._name
    inpmap = dict(to_list(self._inputs))
    keys = list(inpmap.keys())
    keys.sort()
    for inp,par in keys:
      ident += "i_%d_p_%s_%.3e" % (inp,par, \
                                   inpmap[(inp,par)])

    keys = list(self._consts.keys())
    keys.sort()
    for const in keys:
      ident += "c_%s_%.3e" % (const,\
                                   self._consts[const])

    return ident
    #hashstr = str(hash(ident))
    #if '-' in hashstr:
    #  hashstr = hashstr.replace('-','x')
    #return hashstr

  @staticmethod
  def from_json(obj):
    inputs = {}
    for idxstr,data in obj['inputs'].items():
      inputs[int(idxstr)] = data

    entry = MoiraScriptEntry(obj['name'],
                             inputs,
                             obj['consts'],
                             int(obj['output']))
    entry.set_reference(obj['reference'])
    for varname,subobj in obj['ptrs'].items():
      ptr = MoiraScriptEntry.from_json(subobj)
      entry.add_pointer(varname,ptr)

    return entry

  def to_json(self):
    return {
      'name':self._name,
      'ptrs': dict(map(lambda q: (q[0],q[1].to_json()), \
                       self._pointers.items())),
      'consts': self._consts,
      'inputs': self._inputs,
      'output': self._output,
      'reference': self._reference,
      'identifier': self.identifier()
    }

  def __repr__(self):
    return self.identifier()

class MoiraScriptDB:

  def __init__(self,):
    self.paths = MoiraScriptPathHandler()
    path = self.paths.database_file('moira')
    self._db = tdb.TinyDB(path)

  def insert(self,entry):
    assert(isinstance(entry,MoiraScriptEntry))
    q = tdb.Query()
    datum = {
      'identifier': entry.identifier(),
      'name': entry.name,
      'output': entry.output,
      'data': entry.to_json(),
      'script': self.paths.script_file(entry.identifier()),
      'timeseries': self.paths.timeseries_file(entry.identifier())
    }
    self._db.insert(datum)

  def all(self):
      for result in self._db.all():
          yield result

