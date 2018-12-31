import ops
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

    @staticmethod
    def from_json(obj):
        cfg = Config()
        cfg._comp_mode = obj['compute-mode']
        cfg._scale_mode = obj['scale-mode']
        for dac,value in obj['dacs'].items():
            cfg._dacs[dac] = value
        for port,(name,scf,kind_name) in obj['labels'].items():
            cfg._labels[port] = [name,scf,Labels(kind_name)]
        return cfg

    def to_json(self):
        cfg = {}
        cfg['compute-mode'] = self._comp_mode
        cfg['scale-mode'] = self._scale_mode
        cfg['dacs'] = {}
        cfg['labels'] = {}
        for dac,value in self._dacs.items():
            cfg['dacs'][dac] = value

        for port,(name,scf,kind) in self._labels.items():
            cfg['labels'][port] = [name,scf,kind.value]

        return cfg

    def copy(self):
        cfg = Config()
        cfg._comp_mode = self._comp_mode
        cfg._scale_mode = self._scale_mode
        cfg._dacs = dict(self._dacs)
        cfg._labels = dict(self._labels)
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

    def set_label(self,port,name,scf=1.0,kind=Labels.OUTPUT):
        assert(not port in self._labels)
        self._labels[port] = [name,scf,kind]
        return self

    def set_scf(self,port,scf):
        assert(port in self._labels)
        self._labels[port][1] = scf

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
        for port,(name,scf,kind) in self._labels.items():
            yield port,name,scf,kind

    def scf(self,port):
        return self._labels[port][1]

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

class Block:

    ADC = 0
    DAC = 1
    GENERAL = 2
    COPIER = 3
    BUS = 4


    def __init__(self,name,type=None):
        self._name = name
        self._type = type
        # port info
        self._outputs = []
        self._inputs = []

        # mode specific properties
        self._signals = {}
        self._ops = {}
        self._copies = {}

        self._scale_factors = {}
        self._info = {}


        # scale factors
        self._scale_modes = {}
        self.set_comp_modes(['*'])
        self.set_scale_modes("*",['*'])

    def _make_comp_dict(self,comp_mode,d):
        if not comp_mode in d:
            d[comp_mode] = {}

        return d[comp_mode]

    def _make_scale_dict(self,comp_mode,scale_mode,d):
        assert(comp_mode in self._comp_modes)
        data = self._make_comp_dict(comp_mode,d)

        if not scale_mode in data:
            data[scale_mode] = {}

        return data[scale_mode]

    def _get_comp_dict(self,comp_mode,d):
        if not comp_mode in d:
            return None

        return d[comp_mode]

    def _get_scale_dict(self,comp_mode,scale_mode,d):
        data = self._get_comp_dict(comp_mode,d)
        if data is None:
            return None
        if not scale_mode in data:
            return None

        return data[scale_mode]

    def scale_factor(self,comp_mode,scale_mode,out):
        data = self._get_scale_dict(comp_mode,scale_mode, \
                                    self._scale_factors)
        if not out in data:
            return 1.0

        return data[out]

    def set_scale_factor(self,comp_mode,scale_mode,port,value):
        data = self._make_scale_dict(comp_mode,scale_mode,self._scale_factors)
        data[port] = value
        return self

    @property
    def type(self):
        return self._type

    def _map_ports(self,prop,ports):
        for port in ports:
            assert(not port in self._signals)
            self._signals[port] = prop


    def get_dynamics(self,comp_mode,output):
        copy_data = self._get_comp_dict(comp_mode,self._copies)
        op_data = self._get_comp_dict(comp_mode,self._ops)
        if output in copy_data:
            output = copy_data[output]

        return op_data[output]


    def dynamics(self,comp_mode):
        data = self._get_comp_dict(comp_mode,self._ops)
        for output,expr in data.items():
            yield output,expr

    def all_dynamics(self):
        for comp_mode in self._ops:
            for output,expr in self._ops[comp_mode].items():
                yield comp_mode,output,expr

    def signals(self,port):
        return self._signals[port]

    def info(self,comp_mode,scale_mode,port,handle=None):
        data = self._get_scale_dict(comp_mode,scale_mode, \
                                    self._info)
        return data[port][handle]

    def handles(self,comp_mode,port):
        if self.is_input(port):
            return []
        return self.get_dynamics(comp_mode,port).handles()

    @property
    def name(self):
        return self._name

    @property
    def inputs(self):
        return self._inputs

    def by_signal(self,sel_signal,ports):
        def _fn():
            for port in ports:
                signal = self._signals[port]
                if sel_signal == signal:
                    yield port

        return list(_fn())

    def copies(self,comp_mode,port):
        data = self._get_comp_dict(comp_mode,self._copies)
        for this_port, copy_port in data.items():
            if this_port == port:
                yield copy_port

    @property
    def outputs(self):
        return self._outputs

    def add_inputs(self,prop,inps):
        assert(len(inps) > 0)
        for inp in inps:
            self._inputs.append(inp)

        self._map_ports(prop,inps)
        return self

    def add_outputs(self,prop,outs):
        assert(len(outs) > 0)
        self._outputs = outs
        self._map_ports(prop,outs)
        return self


    @property
    def comp_modes(self):
        return self._comp_modes

    def scale_modes(self,comp_mode):
        return self._scale_modes[comp_mode]

    def set_comp_modes(self,modes):
        self._comp_modes = modes
        for mode in modes:
            self._ops[mode] = {}
            self._signals[mode] = {}
            self._copies[mode] = {}
            self._info[mode] = {}
            self._scale_factors[mode] = {}

        return self

    def set_scale_modes(self,comp_mode,modes):
        self._scale_modes[comp_mode] = modes
        for scale_mode in modes:
            self._info[comp_mode][scale_mode] = {}
            self._scale_factors[comp_mode][scale_mode] = {}

        return self

    def set_copy(self,comp_mode,copy,orig):
        data = self._get_comp_dict(comp_mode,self._copies)
        assert(not copy in data)
        data[copy] = orig
        return self

    def set_op(self,comp_mode,out,expr,integrate=False):
        data = self._make_comp_dict(comp_mode,self._ops)
        data[out] = expr
        return self

    def set_info(self,comp_mode,scale_mode,ports,properties,handle=None):
        data = self._make_scale_dict(comp_mode,scale_mode,self._info)

        for port in ports:
            assert(port in self._inputs or port in self._outputs)
            if not port in data:
                data[port] = {}

            assert(not handle in data[port])
            data[port][handle] = properties

        return self


    def is_input(self,port):
        assert(port in self._inputs or port in self._outputs)
        return port in self._inputs

    def is_output(self,port):
        assert(port in self._inputs or port in self._outputs)
        return port in self._outputs

    def _check_comp_dict(self,data):
        for comp_mode in self._comp_modes:
            assert(comp_mode in data)
            yield comp_mode,data[comp_mode]

    def _check_scale_dict(self,data):
        for comp_mode,datum in self._check_comp_dict(data):
            for scale_mode in self._scale_modes[comp_mode]:
                assert(scale_mode in datum)
                yield comp_mode,scale_mode,datum[scale_mode]

    def check(self):
        for comp_mode,data in self._check_comp_dict(self._copies):
            continue

        for comp_mode,_ in self._check_comp_dict(self._ops):
            continue

        for comp_mode in self._comp_modes:
            for out in self._outputs:
                if out in self._copies[comp_mode]:
                    assert(self._copies[comp_mode][out] in self._outputs)
                else:
                    assert(out in self._ops[comp_mode])
                    expr = self._ops[comp_mode][out]
                    for inp in expr.vars():
                        assert(inp in self._inputs)


        for comp_mode,data in self._check_comp_dict(self._signals):
            continue

        for comp_mode,scale_mode,data in self._check_scale_dict(self._info):
            continue

        return self
