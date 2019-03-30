from enum import Enum
from ops.interval import Interval
from ops.bandwidth import Bandwidth
from compiler.common.data_symbolic import SymbolicModel
import ops.op as ops

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
        self._snrs = {}

        # physical model data
        self._gen_delays = {}
        self._prop_delays = {}
        self._mismatch_delays = {}
        self._gen_noise = {}
        self._prop_noise = {}
        self._gen_biases = {}
        self._prop_biases = {}

        # lut models
        self._injs = {}
        self._exprs = {}

    def set_inj(self,port,value):
        self._injs[port] = value

    def inject_var(self,port):
        if not port in self._injs:
            return 1.0
        else:
            return self._injs[port]

    def set_expr(self,port,expr):
        self._exprs[port] = expr

    def exprs(self,inject=True):
        for port in self._exprs.keys():
            expr = self.expr(port,inject=inject)
            yield port,expr

    def expr(self,port,inject=True):
        naked_expr = self._exprs[port]
        if not inject:
            return naked_expr

        repl = {}
        for inj_port,value in self._injs.items():
            repl[inj_port] = ops.Mult(ops.Const(value), \
                                  ops.Var(inj_port))

        inj_out = self._injs[port]
        return ops.Mult(
            ops.Const(inj_out),
            naked_expr.substitute(repl)
        )

    def has_expr(self,port):
        return port in self._exprs

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

        def get_port_dict(data,topobj,objkey,fn=lambda x: x):
            if not objkey in topobj:
                return

            obj = topobj[objkey]
            for port,value in obj.items():
                data[port] = fn(value)

        def get_port_handle_dict(data,topobj,objkey,fn=lambda x: x):
            if not objkey in topobj:
                return

            obj = topobj[objkey]
            for port,datum in obj.items():
                data[port] = {}
                for handle,value in datum.items():
                    handle = None if handle == 'null' else handle
                    data[port][handle] = fn(value)

        get_port_dict(cfg._injs, obj,'injvars')
        get_port_dict(cfg._dacs, obj,'dacs')
        get_port_dict(cfg._labels, obj,'labels', \
                      lambda v: [v[0],Labels(v[1])])
        get_port_handle_dict(cfg._scfs, obj, 'scfs')
        get_port_handle_dict(cfg._intervals, obj, 'intervals', \
                             lambda v: Interval.from_json(v))
        get_port_dict(cfg._snrs, obj, 'snrs')

        get_port_handle_dict(cfg._op_ranges, obj, 'op-ranges', \
                             lambda v: Interval.from_json(v))
        get_port_handle_dict(cfg._bandwidths, obj, 'bandwidths', \
                             lambda v: Bandwidth.from_json(v))
        get_port_dict(cfg._exprs, obj, 'exprs', \
                      lambda v: ops.Op.from_json(v))
        get_port_dict(cfg._gen_noise, obj, 'gen-noise', \
                      lambda v: SymbolicModel.from_json(v))
        get_port_dict(cfg._prop_noise, obj, 'prop-noise', \
                      lambda v: SymbolicModel.from_json(v))
        get_port_dict(cfg._gen_biases, obj,'gen-bias', \
                      lambda v: SymbolicModel.from_json(v))
        get_port_dict(cfg._prop_biases, obj,'prop-bias', \
                      lambda v: SymbolicModel.from_json(v))
        get_port_dict(cfg._gen_delays, obj,'gen-delay', \
                      lambda v: SymbolicModel.from_json(v))
        get_port_dict(cfg._prop_delays, obj,'prop-delay', \
                      lambda v: SymbolicModel.from_json(v))
        #get_port_dict(cfg._mismatch_delays, obj,'mismatch-delay')
        return cfg

    def to_json(self):
        cfg = {}
        cfg['compute-mode'] = self._comp_mode
        cfg['scale-mode'] = self._scale_mode

        def set_port_dict(key,data,fn=lambda x: x):
            cfg[key] = {}
            for port,value in data.items():
                cfg[key][port] = fn(value)

        def set_port_handle_dict(key,data,fn=lambda x: x):
            cfg[key] = {}
            for port,datum in data.items():
                cfg[key][port] = {}
                for handle,value in datum.items():
                    cfg[key][port][handle] = fn(value)

        set_port_dict('injvars',self._injs)
        set_port_dict('dacs',self._dacs)
        set_port_dict('labels', self._labels,
                      lambda args: [args[0],args[1].value])

        set_port_handle_dict('scfs',self._scfs)
        set_port_handle_dict('intervals',self._intervals, \
                             lambda value: value.to_json())
        set_port_dict('snrs',self._snrs)
        set_port_handle_dict('op-ranges', self._op_ranges, \
                             lambda value: value.to_json())
        set_port_handle_dict('bandwidths', self._bandwidths, \
                             lambda value: value.to_json())

        set_port_dict('exprs',self._exprs,
                      lambda value: value.to_json())
        set_port_dict('gen-noise',self._gen_noise,
                      lambda value: value.to_json())
        set_port_dict('prop-noise',self._prop_noise,
                      lambda value: value.to_json())
        set_port_dict('gen-bias',self._gen_biases,
                      lambda value: value.to_json())
        set_port_dict('prop-bias',self._prop_biases,
                      lambda value: value.to_json())
        set_port_dict('gen-delay',self._gen_delays,
                      lambda value: value.to_json())
        set_port_dict('prop-delay',self._prop_delays,
                      lambda value: value.to_json())
        set_port_dict('mismatch-delay',self._mismatch_delays)

        return cfg

    def copy(self):
      cfg = Config()
      cfg._comp_mode = self._comp_mode
      cfg._scale_mode = self._scale_mode
      cfg._dacs = dict(self._dacs)
      cfg._labels = dict(self._labels)
      cfg._scfs = dict(self._scfs)
      cfg._intervals = dict(self._intervals)
      cfg._snrs = dict(self._snrs)
      cfg._bandwidths = dict(self._bandwidths)
      cfg._op_ranges = dict(self._op_ranges)
      cfg._exprs = dict(self._exprs)
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

    def generated_noises(self):
        for port,noise in self._gen_noise.items():
            yield port,noise

    def propagated_noise(self,port):
      if not port in self._prop_noise:
          return None
      return self._prop_noise[port]

    def propagated_noises(self):
        for port,value in self._prop_noise.items():
            yield port,value

    def propagated_bias(self,port):
      if not port in self._prop_biases:
          return None
      return self._prop_biases[port]

    def propagated_biases(self):
        for port,value in self._prop_biases.items():
            yield port,value

    def generated_bias(self,port):
      if not port in self._gen_biases:
          return None
      return self._gen_biases[port]

    def generated_biases(self):
        for port,bias in self._gen_biases.items():
            yield port,bias

    def propagated_delay(self,port):
      if not port in self._prop_delays:
          return None
      return self._prop_delays[port]

    def propagated_delays(self):
        for port,delay in self._prop_delays.items():
            yield port,delay

    def delay_mismatch(self,port):
      if not port in self._mismatch_delays:
          return None
      return self._mismatch_delays[port]

    def delay_mismatches(self):
        for port,value in self._mismatch_delays.items():
            yield port,value

    def generated_delay(self,port):
      if not port in self._gen_delays:
          return None
      return self._gen_delays[port]

    def generated_delays(self):
        for port,delay in self._gen_delays.items():
            yield port,delay

    def set_propagated_noise(self,port,noise):
      assert(noise.is_posynomial())
      self._prop_noise[port] = noise

    def set_propagated_bias(self,port,bias):
        if not (bias.is_posynomial()):
            raise Exception("not posynomial: %s" % bias)

        self._prop_biases[port] = bias

    def set_delay_mismatch(self,port,delay):
      assert(delay.is_posynomial())
      self._mismatch_delays[port] = delay

    def set_propagated_delay(self,port,delay):
      assert(delay.is_posynomial())
      self._prop_delays[port] = delay

    def set_generated_noise(self,port,noise):
      if not (noise.is_posynomial()):
          raise Exception("not posynomial: %s" % noise)

      self._gen_noise[port] = noise

    def set_generated_bias(self,port,bias):
      if not (bias.is_posynomial()):
          raise Exception("not posynomial: %s" % bias)

      self._gen_biases[port] = bias

    def set_generated_delay(self,port,delay):
      assert(delay.is_posynomial())
      self._gen_delays[port] = delay

    def clear_noise_model(self):
        def reset(key):
            setattr(self,key,{})

        reset('_gen_noise')
        reset('_prop_noise')

    def clear_physical_model(self):
        def reset(key):
            setattr(self,key,{})

        reset('_gen_delays')
        reset('_gen_noise')
        reset('_gen_biases')
        reset('_prop_delays')
        reset('_prop_biases')
        reset('_prop_noise')


    def has_physical_model(self):
        def test(key):
            if len(getattr(self,key).keys()) == 0:
                return False
            else:
                return True

        return test('_gen_delays') and \
            test('_gen_noise') and \
            test('_gen_biases') and  \
            test('_prop_delays') and \
            test('_prop_biases') and \
            test('_prop_noise')

    def set_bandwidth(self,port,bandwidth,handle=None):
      self._make(self._bandwidths,port)
      assert(not bandwidth is None)
      self._bandwidths[port][handle] = bandwidth


    def set_op_range(self,port,op_range,handle=None):
      self._make(self._op_ranges,port)
      assert(isinstance(op_range,Interval))
      self._op_ranges[port][handle] = op_range


    def set_snr(self,port,snr):
      self._snrs[port] = snr

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


    def snr(self,port,handle=None):
      if not port in self._snrs:
        return None

      return self._snrs[port]


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


    def snrs(self):
      snrs = {}
      for port,snr in self._snrs.items():
          snrs[port] = snr

      return snrs


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

