from enum import Enum


class Labels(Enum):
    CONST_INPUT = 'const-inp';
    DYNAMIC_INPUT = 'dyn-inp';
    OUTPUT = 'out'

class Config:

    def __init__(self):
        self._comp_mode = None
        self._scale_mode = None
        self._dacs = {}
        self._labels = {}
        self._scfs = {}

    @staticmethod
    def from_json(obj):
        cfg = Config()
        cfg._comp_mode = obj['compute-mode']
        cfg._scale_mode = obj['scale-mode']
        for dac,value in obj['dacs'].items():
            cfg._dacs[dac] = value
        for port,(name,scf,kind_name) in obj['labels'].items():
            cfg._labels[port] = [name,Labels(kind_name)]
        for port,scf in obj['scfs'].items():
            cfg._scfs[port] = scf
        return cfg

    def to_json(self):
        cfg = {}
        cfg['compute-mode'] = self._comp_mode
        cfg['scale-mode'] = self._scale_mode
        cfg['dacs'] = {}
        cfg['scfs'] = {}
        cfg['labels'] = {}
        for dac,value in self._dacs.items():
            cfg['dacs'][dac] = value
        for port,(name,kind) in self._labels.items():
            cfg['labels'][port] = [name,kind.value]
        for port,scf in self._scfs.items():
            cfg['scfs'][port] = scf

        return cfg

    def copy(self):
      cfg = Config()
      cfg._comp_mode = self._comp_mode
      cfg._scale_mode = self._scale_mode
      cfg._dacs = dict(self._dacs)
      cfg._labels = dict(self._labels)
      cfg._scfs = dict(self._scfs)
      return cfg

    @property
    def scale_mode(self):
      return self._scale_mode

    @property
    def comp_mode(self):
      return self._comp_mode

    def set_scale_mode(self,modename):
      self._scale_mode = modename
      return self

    def has_dac(self,v):
      return v in self._dacs

    def dac(self,v):
      return self._dacs[v]

    def set_comp_mode(self,modename):
      self._comp_mode = modename
      return self

    def set_dac(self,dac,value):
      self._dacs[dac] = value
      return self

    def set_label(self,port,name,kind=Labels.OUTPUT):
      assert(not port in self._labels)
      self._labels[port] = [name,kind]
      return self

    def set_scf(self,port,scf):
      assert(port in self._scfs)
      self._scfs[port] = scf

    def has_label(self,port):
      return port in self._labels

    def label(self,port):
      return self._labels[port][0]

    def label_type(self,port):
      return self._labels[port][2]

    def values(self):
      for dac,value in self._dacs.items():
        yield dac,value

    def labels(self):
      for port,(name,kind) in self._labels.items():
        yield port,name,kind

    def scf(self,port):
      if not port in self._scfs:
        return 1.0

      return self._scfs[port]

    def to_str(self,delim="\n"):
        s = ""
        s += "comp-mode: %s" % self._comp_mode
        s += delim
        s += "scale-mode: %s" % str(self._scale_mode)
        s += delim
        for v,e in self._dacs.items():
            s += "%s: %s" % (v,e)
            s += delim

        for l,(n,scf,k) in self._labels.items():
            s += "%s:[lbl=%s,scf=%s,kind=%s]" % (l,n,scf,k)
            s += delim

        return s

    def __repr__(self):
        return self.to_str()

