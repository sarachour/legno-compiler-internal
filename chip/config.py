from enum import Enum
from ops.interval import Interval

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
        # scaling factors on ports
        self._scfs = {}
        # time scaling factor
        self._taus = {}
        # hardware interval
        self._op_ranges= {}
        # unscaled math interval
        self._intervals = {}
        # unscaled bandwidth
        self._bandwidths = {}

    def dynamics(self,block,port):
      assert(not self._comp_mode is None)
      assert(not self._scale_mode is None)
      return block.get_dynamics(self._comp_mode,port, \
                                scale_mode=self._scale_mode)

    def props(self,block,port,handle=None):
      assert(not self._comp_mode is None)
      assert(not self._scale_mode is None)
      return block.props(self._comp_mode,self._scale_mode,port,handle=handle)


    def coeff(self,block,port):
      assert(not self._comp_mode is None)
      assert(not self._scale_mode is None)
      return block.coeff(self._comp_mode,self._scale_mode,port)

    @staticmethod
    def from_json(obj):
        cfg = Config()
        cfg._comp_mode = obj['compute-mode']
        cfg._scale_mode = obj['scale-mode']
        for dac,value in obj['dacs'].items():
          cfg._dacs[dac] = value
        for port,(name,kind_name) in obj['labels'].items():
          cfg._labels[port] = [name,Labels(kind_name)]
        for port,scf in obj['scfs'].items():
          cfg._scfs[port] = scf
        for port,ival in obj['intervals'].items():
          cfg._intervals[port] = Interval.from_json(ival)
        for port,ival in obj['op-ranges'].items():
          cfg._op_ranges[port] = Interval.from_json(ival)
        for port,bandwidth in obj['bandwidths'].items():
          cfg._bandwidths[port] = bandwidth
        for port,tau in obj['taus'].items():
          cfg._tau[port] = tau

        return cfg

    def to_json(self):
        cfg = {}
        cfg['compute-mode'] = self._comp_mode
        cfg['scale-mode'] = self._scale_mode
        cfg['dacs'] = {}
        cfg['scfs'] = {}
        cfg['taus'] = {}
        cfg['labels'] = {}
        cfg['intervals'] = {}
        cfg['op-ranges'] = {}
        cfg['bandwidths'] = {}

        for dac,value in self._dacs.items():
            cfg['dacs'][dac] = value
        for port,(name,kind) in self._labels.items():

            cfg['labels'][port] = [name,kind.value]
        for port,scfs in self._scfs.items():
          cfg['scfs'][port] = {}
          for handle,scf in scfs.items():
            cfg['scfs'][port][handle] = scf

        for port,taus in self._taus.items():
          cfg['taus'][port] = {}
          for handle,tau in taus.items():
            cfg['taus'][port][handle] = scf

        for port,ivals in self._intervals.items():
          cfg['intervals'][port] = {}
          for handle,ival in ivals.items():
            cfg['intervals'][port][handle] = ival.to_json()

        for port,oprngs in self._op_ranges.items():
          cfg['op-ranges'][port] = {}
          for handle,oprng in oprngs.items():
            cfg['op-ranges'][port][handle] = oprng.to_json()

        for port,bws in self._bandwidths.items():
          cfg['bandwidths'][port] = {}
          for handle,bw in bws .items():
            cfg['bandwidths'][port][handle] = bw


        return cfg

    def copy(self):
      cfg = Config()
      cfg._comp_mode = self._comp_mode
      cfg._scale_mode = self._scale_mode
      cfg._dacs = dict(self._dacs)
      cfg._labels = dict(self._labels)
      cfg._scfs = dict(self._scfs)
      cfg._taus = dict(self._taus)
      cfg._intervals = dict(self._intervals)
      cfg._bandwidths = dict(self._bandwidths)
      cfg._op_ranges = dict(self._op_ranges)
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
      if not v in self._dacs:
        return None

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

    def _make(self,dict_,port):
      if not port in dict_:
        dict_[port] = {}

    def set_tau(self,port,tau,handle=None):
      self._make(self._taus,port)
      self._taus[port][handle] = tau


    def set_bandwidth(self,port,bandwidth,handle=None):
      self._make(self._bandwidths,port)
      self._bandwidths[port][handle] = interval


    def set_op_range(self,port,op_range,handle=None):
      self._make(self._op_ranges,port)
      assert(isinstance(op_range,Interval))
      self._op_ranges[port][handle] = op_range


    def set_interval(self,port,interval,handle=None):
      self._make(self._intervals,port)
      self._intervals[port][handle] = interval

    def set_scf(self,port,scf,handle=None):
      self._make(self._scfs,port)
      self._scfs[port][handle] = scf

    def has_label(self,port):
      return port in self._labels

    def label(self,port):
      return self._labels[port][0]

    def label_type(self,port):
      return self._labels[port][1]

    def values(self):
      for dac,value in self._dacs.items():
        yield dac,value

    def labels(self):
      for port,(name,kind) in self._labels.items():
        yield port,name,kind

    def bandwidth(self,port,handle=None):
      if not port in self._bandwidths or \
         not handle in self._bandwidths[port]:
        return None

      return self._bandwidths[port][handle]

    def op_range(self,port,handle=None):
      if not port in self._op_ranges or \
         not handle in self._op_ranges[port]:
        return None

      return self._op_ranges[port][handle]


    def interval(self,port,handle=None):
      if not port in self._intervals or \
         not handle in self._intervals[port]:
        return None

      return self._intervals[port][handle]

    def intervals(self):
      intervals = {}
      for port,handles in self._intervals.items():
        for handle,ival in handles.items():
          if handle is None:
            intervals[port] = ival
          else:
            assert(not handle in intervals)
            intervals[handle] = ival

      return intervals

    def tau(self,port,handle=None):
      if not port in self._taus or \
         not handle in self._taus[port]:
        return None

      return self._taus[port][handle]

    def scf(self,port,handle=None):
      if not port in self._scfs or \
         not handle in self._scfs[port]:
        return None

      return self._scfs[port][handle]

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

