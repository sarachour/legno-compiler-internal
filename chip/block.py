import ops

class Labels:

    CONST_INPUT = 0;
    DYNAMIC_INPUT = 1;
    OUTPUT = 2

    @staticmethod
    def to_str(idx):
        if idx == Labels.CONST_INPUT:
            return "const-inp"
        elif idx == Labels.DYNAMIC_INPUT:
            return "dyn-inp"
        elif idx == Labels.OUTPUT:
            return "out"
        else:
            raise Exception("unknown label ident <%d>" % idx)

class Config:

    def __init__(self):
        self._mode = "default"
        self._scale_mode = "default"
        self._dacs = {}
        self._labels = {}

    def to_json(self):
        cfg = {}
        cfg['compute-mode'] = self._mode
        cfg['scale-mode'] = self._scale_mode
        cfg['dacs'] = {}
        cfg['labels'] = {}
        for dac,value in self._dacs.items():
            cfg['dacs'][dac] = value

        for port,label in self._labels.items():
            cfg['labels'][port] = label

        return cfg

    def copy(self):
        cfg = Config()
        cfg._mode = self._mode
        cfg._scale_mode = self._scale_mode
        cfg._dacs = dict(self._dacs)
        cfg._labels = dict(self._labels)
        return cfg

    @property
    def scale_mode(self):
        return self._scale_mode

    @property
    def mode(self):
        return self._mode

    def set_scale_mode(self,modename):
        self._scale_mode = modename
        return self

    def has_dac(self,v):
        return v in self._dacs

    def dac(self,v):
        return self._dacs[v]

    def set_mode(self,modename):
        self._mode = modename
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
        s += "comp-mode: %s" % self._mode
        s += delim
        s += "scale-mode: %s" % self._scale_mode
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
        self._sigmap = {}
        self._external = False

        # mode specific properties
        self._modes = ['default']
        self._current_mode = 'default'
        self._propmap = {}
        self._integ = {}
        self._copies = {}
        self._ops = {}


        # scale factors
        self._scale_modes = ['default']
        self._current_scale_mode = 'default'
        self._scale_factors = {}


    def integrator(self,out,mode=None):
        mode = self._current_mode if mode is None else mode
        return self._integ[out][mode]

    def set_external(self):
        self._external = True
        return self

    def set_scale_modes(self,modes):
        assert(not "default" in modes)
        self._scale_modes = modes
        self._current_scale_mode = None
        for scale_mode in self._scale_modes:
            self._scale_factors[str(scale_mode)] = {}

        return self

    def set_scale_mode(self,mode):
        assert(mode in self._scale_modes)
        self._current_scale_mode = mode
        return self

    def scale_factor(self,out,mode=None):
        mode = self._current_scale_mode \
               if mode is None else str(mode)

        if not mode in self._scale_factors:
            return 1.0

        if not out in self._scale_factors[mode]:
            return 1.0

        return self._scale_factors[mode][out]

    def set_scale_factor(self,port,value):
        mode = self._current_scale_mode
        mode_key = str(mode)
        if not mode_key in self._scale_factors:
            self._scale_factors[mode_key] = {}

        self._scale_factors[mode_key][port] = value
        return self

    @property
    def type(self):
        return self._type

    def _map_ports(self,prop,ports):
        for port in ports:
            assert(not port in self._sigmap)
            self._sigmap[port] = prop


    def dynamics(self,mode=None):
        for output,modedict in self._ops.items():
            if not mode is None:
                expr = modedict[mode]
                yield output,expr
                continue

            for _mode,expr in modedict.items():
                yield output,_mode,expr

    def signals(self,port):
        return self._sigmap[port]

    def props(self,mode,port):
        return self._propmap[mode][port]


    @property
    def name(self):
        return self._name

    @property
    def inputs(self):
        return self._inputs

    def by_property(self,sel_prop,mode,ports):
        def _fn():
            for port in ports:
                prop = self._sigmap[port]
                if sel_prop == prop:
                    yield port

        return list(_fn())

    def copies(self,mode,port):
        mode = "default" if mode is None else mode

        for copy_port, srcdict in self._copies.items():
            if not mode in srcdict:
                continue

            if srcdict[mode] == port:
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

    def set_mode(self,mode):
        assert(mode in self._modes)
        self._current_mode = mode
        return self

    @property
    def modes(self):
        return self._modes

    @property
    def scale_modes(self):
        return self._scale_modes

    def set_modes(self,modes):
        self._modes = modes
        self._current_mode = None
        return self

    def set_copy(self,copy,orig):
        mode = self._current_mode
        if not copy in self._copies:
            self._copies[copy] = {}

        self._copies[copy][mode] = orig
        return self

    def set_op(self,out,expr,integrate=False):
        assert(not self._current_mode is None)
        if not out in self._ops:
            self._ops[out] = {}
            self._integ[out] = {}

        assert(not self._current_mode in self._ops[out])
        self._ops[out][self._current_mode] = expr
        self._integ[out][self._current_mode] = integrate
        return self

    def set_prop(self,ports,properties):
        mode = self._current_mode
        for port in ports:
            assert(port in self._inputs or port in self._outputs)
            assert(not port in self._propmap)
            if not mode in self._propmap:
                self._propmap[mode] = {}

            self._propmap[mode][port] = properties

        return self


    def is_input(self,port):
        assert(port in self._inputs or port in self._outputs)
        return port in self._inputs

    def is_output(self,port):
        assert(port in self._inputs or port in self._outputs)
        return port in self._outputs

    def check(self):
        for inp in self._inputs:
            for mode in self._modes:
                assert(inp in self._sigmap)
                assert(inp in self._propmap[mode])


        for out in self._outputs:
            assert(out in self._ops or out in self._copies)
            assert(out in self._sigmap)

            for mode in self._modes:
                assert(mode in self._propmap)
                assert(out in self._propmap[mode])
                if out in self._copies \
                   and mode in self._copies[out]:
                    assert(self._copies[out][mode] in self._outputs)

                else:
                    assert(mode in self._ops[out])
                    assert(mode in self._integ[out])
                    expr = self._ops[out][mode]
                    inps = expr.vars()
                    for inp in inps:
                        assert(inp in self._inputs)

        return self
