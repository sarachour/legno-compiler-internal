from enum import Enum
from ops.interval import Interval
from ops.bandwidth import Bandwidth

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
        # hardware interval
        self._op_ranges= {}
        # (scaled) math interval
        self._intervals = {}
        # (scaled) bandwidth
        self._bandwidths = {}

        self._gen_delays = {}
        self._prop_delays = {}
        self._mismatch_delays = {}
        self._gen_noise = {}
        self._prop_noise = {}
        self._gen_biases = {}
        self._prop_biases = {}

    def dynamics(self,block,port):
      assert(not self._comp_mode is None)
      assert(not self._scale_mode is None)
      return block.get_dynamics(self._comp_mode,port, \
                                scale_mode=self._scale_mode)

    def physical(self,block,port,handle=None):
      assert(not self._comp_mode is None)
      assert(not self._scale_mode is None)
      return block.physical(self._comp_mode,self._scale_mode,port)


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
        if isinstance(cfg._comp_mode, list):
            cfg._comp_mode = tuple(cfg._comp_mode)

        cfg._scale_mode = obj['scale-mode']
        if isinstance(cfg._scale_mode, list):
            cfg._scale_mode = tuple(cfg._scale_mode)

        for dac,value in obj['dacs'].items():
          cfg._dacs[dac] = value
        for port,(name,kind_name) in obj['labels'].items():
          cfg._labels[port] = [name,Labels(kind_name)]

        for port,scfs in obj['scfs'].items():
          cfg._scfs[port] = {}
          for handle,scf in scfs.items():
            handle = None if handle == 'null' else handle
            cfg._scfs[port][handle] = scf

        for port,ivals in obj['intervals'].items():
          cfg._intervals[port] = {}
          for handle,ival in ivals.items():
            handle = None if handle == 'null' else handle
            cfg._intervals[port][handle] = Interval.from_json(ival)

        for port,ivals in obj['op-ranges'].items():
          cfg._op_ranges[port] = {}
          for handle,ival in ivals.items():
            handle = None if handle == 'null' else handle
            cfg._op_ranges[port][handle] = Interval.from_json(ival)

        for port,bandwidths in obj['bandwidths'].items():
          cfg._bandwidths[port] = {}
          for handle,bandwidth in bandwidths.items():
            handle = None if handle == 'null' else handle
            cfg._bandwidths[port][handle] = Bandwidth.from_json(bandwidth)

        return cfg

    def to_json(self):
        cfg = {}
        cfg['compute-mode'] = self._comp_mode
        cfg['scale-mode'] = self._scale_mode
        cfg['dacs'] = {}
        cfg['scfs'] = {}
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
            cfg['bandwidths'][port][handle] = bw.to_json()


        return cfg

    def copy(self):
      cfg = Config()
      cfg._comp_mode = self._comp_mode
      cfg._scale_mode = self._scale_mode
      cfg._dacs = dict(self._dacs)
      cfg._labels = dict(self._labels)
      cfg._scfs = dict(self._scfs)
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

    def clear_bandwidths(self):
      self._bandwidths = {}

    def clear_intervals(self):
      self._intervals = {}

    def generated_noise(self,port):
      if not port in self._gen_noise:
          return None
      return self._gen_noise[port]


    def propagated_biases(self):
      bss = {}
      for port, bs in self._prop_biases.items():
        bss[port] = bs

      return bss


    def delay_mismatches(self):
      delays = {}
      for port,delay in self._mismatch_delays.items():
        delays[port] = delay

      return delays


    def propagated_delays(self):
      delays = {}
      for port,delay in self._prop_delays.items():
        delays[port] = delay

      return delays


    def propagated_noises(self):
      nzs = {}
      for port, nz in self._prop_noise.items():
        nzs[port] = nz

      return nzs

    def propagated_noise(self,port):
      if not port in self._prop_noise:
          return None
      return self._prop_noise[port]


    def propagated_noise(self,port):
      if not port in self._prop_noise:
          return None
      return self._prop_noise[port]

    def propagated_bias(self,port):
      if not port in self._prop_biases:
          return None
      return self._prop_biases[port]


    def generated_bias(self,port):
      if not port in self._gen_biases:
          return None
      return self._gen_biases[port]

    def propagated_delay(self,port):
      if not port in self._prop_delays:
          return None
      return self._prop_delays[port]


    def delay_mismatch(self,port):
      if not port in self._mismatch_delays:
          return None
      return self._mismatch_delays[port]


    def generated_delay(self,port):
      if not port in self._gen_delays:
          return None
      return self._gen_delays[port]

    def set_propagated_noise(self,port,noise):
      self._prop_noise[port] = noise

    def set_propagated_bias(self,port,bias):
      self._prop_biases[port] = bias

    def set_delay_mismatch(self,port,delay):
      self._mismatch_delays[port] = delay

    def set_propagated_delay(self,port,delay):
      self._prop_delays[port] = delay

    def set_generated_noise(self,port,noise):
      self._gen_noise[port] = noise

    def set_generated_bias(self,port,bias):
      self._gen_biases[port] = bias

    def set_generated_delay(self,port,delay):
      self._gen_delays[port] = delay

    def set_bandwidth(self,port,bandwidth,handle=None):
      self._make(self._bandwidths,port)
      assert(not bandwidth is None)
      self._bandwidths[port][handle] = bandwidth


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

    def op_range(self,port,handle=None):
      if not port in self._op_ranges or \
         not handle in self._op_ranges[port]:
        return None

      return self._op_ranges[port][handle]


    def bandwidth(self,port,handle=None):
      if not port in self._bandwidths or \
         not handle in self._bandwidths[port]:
        return None

      return self._bandwidths[port][handle]


    def interval(self,port,handle=None):
      if not port in self._intervals or \
         not handle in self._intervals[port]:
        return None

      return self._intervals[port][handle]


    def bandwidths(self):
      bandwidths = {}
      for port,handles in self._bandwidths.items():
        for handle,bw in handles.items():
          if handle is None:
            bandwidths[port] = bw
          else:
            assert(not handle in bandwidths)
            bandwidths[handle] = bw

      return bandwidths


    def bandwidths(self,time_constant=1.0):
      bandwidths = {}
      for port,handles in self._bandwidths.items():
        for handle,bw in handles.items():
          if handle is None:
            bandwidths[port] = bw.timescale(1.0/time_constant)
          else:
            assert(not handle in bandwidths)
            bandwidths[handle] = bw.timescale(1.0/time_constant)

      return bandwidths


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

    def has_scf(self,port,handle=None):
      if not port in self._scfs or \
         not handle in self._scfs[port]:
        return False
      return True

    def scf(self,port,handle=None):
      if not port in self._scfs or \
         not handle in self._scfs[port]:
        return None

      return self._scfs[port][handle]

    def to_str(self,delim="\n"):
        s = ""
        s += "comp-mode: %s" % str(self._comp_mode)
        s += delim
        s += "scale-mode: %s" % str(self._scale_mode)
        s += delim
        for v,e in self._dacs.items():
            s += "%s: %s" % (v,e)
            s += delim

        s += delim
        for l,(n,k) in self._labels.items():
            s += "%s:[lbl=%s,kind=%s]" % (l,n,k)
            s += delim

        s += delim
        for p,scfs in self._scfs.items():
          for handle,scf in scfs.items():
            s += "scf %s[%s]: %s" % (p,handle,scf)
            s += delim

        for p,intervals in self._intervals.items():
          for handle,ival in intervals.items():
            s += "ival %s[%s]: %s" % (p,handle,ival)
            s += delim

        for p,bandwidths in self._bandwidths.items():
          for handle, bw in bandwidths.items():
            s += "bw %s[%s]: %s" % (p,handle,bw)
          s += delim

        return s

    def __repr__(self):
        return self.to_str()

