
class XStmt:
    DUP_SIGNAL = 0;

    def __init__(self,type):
        self._type = type

    def apply(self,ctx):
        raise NotImplementedError

class XSFreqShift(XStmt):

    def __init__(self,index,scale,offset):
        XStmt.__init__(self,XStmt.FREQ_SCALE)
        self._index = index
        self._scale = scale
        self._offset = offset

    def apply(self,ctx,varmap):
        phasor_train = ctx.get(self._index)
        for phasor in phasor_train:
            new_freq = phasor.freq*self._scale + self._offset
            phasor.set_freq(new_freq)

        phasor_train._reorder_freq()

class XSMagnitudeScale(XStmt):


    def __init__(self,index,scale,offset):
        XStmt.__init__(self,XStmt.MAG_SCALE)
        self._index = index
        self._scale = scale
        self._offset = offset

    def apply(self,ctx,varmap):
        phasor_train = ctx.get(self._index)
        for phasor in phasor_train:
            new_mag= phasor.magnitude*self._scale + self._offset
            phasor.set_magnitude(new_magnitude)


class XSPhaseScale(XStmt):

    def __init__(self,index,scale,offset):
        XStmt.__init__(self,XStmt.PHASE_SCALE)
        self._index = index
        self._scale = scale
        self._offset = offset

    def apply(self,ctx,varmap):
        phasor_train = ctx.get(self._index)
        for phasor in phasor_train:
            new_phase = phasor.phase*self._scale + self._offset
            phasor.set_phase(new_phase)

class XSDupSignal(XStmt):

    def __init__(self,variable,idx):
        XStmt.__init__(XStmt.DUP_SIGNAL)
        self._variable = variable
        self._idx = idx

    def apply(self,ctx,varmap):
        ctx.bind(self._idx,varmap[self._variable].copy())



class XSConstant(XForm):

    def __init__(self,min_freq,max_freq,magnitude,phase):
        XStmt.__init__(self,XStmt.CONSTANT)
        self._min_freq = min_freq
        self._max_freq = max_freq
        self._magnitude = magnitude
        self._phase = phase

    def apply(self,ctx,varmap):
        ctx.add_const(self._min_freq,self._max_freq,
                      self._magnitude,self._phase)

class NoiseModel:

    SHAPE_GAUSSIAN = 0
    SHAPE_POISSON = 1

    class Context:

        def __init__(self):
            self._vars = {}
            self._consts = []

        def add_const(self,fmin,fmax,mag,phase):
            self._consts.append((fmin,fmax,mag,phase))

        def bind_var(self,idx,phasor_train):
            assert(not idx in self._vars)
            self._vars[idx] = phasor_train

        def get(self,idx):
            return self._vars[idx]

        def compute(self):
            raise NotImplementedError

    def __init__(self,shape):
        self._prog = []
        self._model = None
        self._shape = shape

    def attach_model(self,model):
        self._model = model

    def add_stmt(self,stmt):
        assert(isinstance(stmt,XStmt))
        self._prog.append(stmt)

    def execute(self,variables):
        ctx = NoiseModel.Context()
        for stmt in self._prog:
            stmt.apply(ctx,variables)

        return ctx.compute()
