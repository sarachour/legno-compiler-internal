from ops.interval import Interval

class MathProg:

    def __init__(self,name):
        self._name = name
        self._bindings = {}
        self._intervals = {}
        self._bandwidths= {}

    def bind(self,var,expr):
        assert(not var in self._bindings)
        self._bindings[var] = expr

    def bindings(self):
        for var,expr in self._bindings.items():
            yield var,expr


    def interval(self,v,min_v,max_v):
        assert(min_v <= max_v)
        self._intervals[v] = Interval.type_infer(min_v,max_v)

    def intervals(self):
        for v,ival in self._intervals.items():
            yield v,ival

    def bandwidths(self):
        for v,bw in self._bandwidths.items():
            yield v,bw

    def compile(self):
        for variable in self._bindings:
            assert(variable in self._intervals)

        for variable,expr in self._bindings.items():
            if expr is None:
                continue
            bw = expr.bandwidth(self._intervals,self._bindings)
            self._bandwidths[variable] = bw

    @property
    def name(self):
        return self._name

class StochMathProg:

    class Distribution:
        GAUSSIAN = 0

    class Operator:
        EQUALS = 0
        LESS_THAN = 1

    def __init__(self,name):
        MathProg.__init__(self,name)
        self._stoch = {}

    def bind_stoch(self,var,variance,dist,op):
        self._stoch[var] = (variance,dist,op)
