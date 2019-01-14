from ops.interval import Interval
from ops.bandwidth import Bandwidth
import util.util as util

class MathEnv:

    def __init__(self,name):
        self._name = name
        self._sim_time = 1.0
        self._input_time = 1.0
        self._inputs = {}

    def input(self,name):
        return self._inputs[name]

    def set_input(self,name,func,periodic=False):
        self._inputs[name] = (func,periodic)

    @property
    def name(self):
        return self._name

    @property
    def input_time(self):
        return self._input_time

    @property
    def sim_time(self):
        return self._sim_time

    def set_input_time(self,t):
        assert(t > 0)
        self._input_time = t


    def set_sim_time(self,t):
        assert(t > 0)
        self._sim_time = t

class MathProg:

    def __init__(self,name):
        self._name = name
        self._bindings = {}
        self._intervals = {}
        self._bandwidths= {}
        self._variables = []

    def variables(self):
        return self._variables

    def bind(self,var,expr):
        assert(not var in self._bindings)
        self._variables.append(var)
        self._bindings[var] = expr

    def bindings(self):
        for var,expr in self._bindings.items():
            yield var,expr

    def binding(self,v):
        if not v in self._bindings:
            return None
        return self._bindings[v]

    def interval(self,v):
        return self._intervals[v]

    def bandwidth(self,v):
        return self._bandwidths[v]

    def set_bandwidth(self,v,b):
        if not v in self._variables:
            self._variables.append(v)
        self._bandwidths[v] = Bandwidth(b)

    def set_interval(self,v,min_v,max_v):
        assert(min_v <= max_v)
        if not v in self._variables:
            self._variables.append(v)
        self._intervals[v] = Interval.type_infer(min_v,max_v)

    def intervals(self):
        for v,ival in self._intervals.items():
            yield v,ival

    def bandwidths(self):
        for v,bw in self._bandwidths.items():
            yield v,bw

    def compile(self):
        for variable,expr in self._bindings.items():
            if not (variable in self._intervals):
                if expr is None:
                    raise Exception("cannot infer ival: <%s> has no expression" \
                                    % variable)

                icoll = expr.interval(self._intervals)
                self._intervals[v] = icoll.interval


        progress = True
        while progress:
            progress = False
            for variable,expr in self._bindings.items():
                if not (variable in self._bandwidths):
                    if expr is None:
                        raise Exception("cannot infer bw: <%s> has no expression" \
                                        % variable)

                    deps = expr.bwvars()
                    if util.keys_in_dict(deps,self._bandwidths):
                        new_ivals = expr.infer_interval(self._intervals[variable], \
                                                        self._intervals)

                        ival_dict = new_ivals.merge_dict(self._intervals).dict()
                        bwcoll = expr.infer_bandwidth(ival_dict,bandwidths=self._bandwidths)
                        self._bandwidths[variable] = bwcoll.bandwidth
                        progress = True

        assert(util.keys_in_dict(self._bindings.keys(), self._bandwidths))
        assert(util.keys_in_dict(self._bindings.keys(), self._intervals))
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
