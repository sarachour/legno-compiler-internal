from ops.interval import Interval
from ops.bandwidth import Bandwidth, BandwidthCollection
import util.util as util
import sys
from enum import Enum
import ops.op as op

class MathEnv:

    def __init__(self,name):
        self._name = name
        self._sim_time = 1.0
        self._input_time = 1.0
        self._inputs = {}

    def input(self,name):
        if not name in self._inputs:
            raise Exception("input not recognized: %s" % name)
        return self._inputs[name][0]

    def is_periodic(self,name):
        return self._inputs[name][1]

    def set_input(self,name,func,periodic=False):
        assert(isinstance(func,op.Op))
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
    class ExprType(Enum):
        INTEG = "integ"
        EXTERN = "extern"
        FN = "fn"

    def __init__(self,name):
        self._name = name
        self._bindings = {}
        self._intervals = {}
        self._bandwidths= {}
        self._variables = []
        self._snr = {}
        self._analog_snr= 5.0
        self._digital_snr= 5.0
        self._max_sim_time = 1.0

        self.__order = None
        self.__order_integs = None
        self.__types = None

    def digital_snr(self):
        return self._digital_snr

    def analog_snr(self):
        return self._analog_snr

    def set_analog_snr(self,v):
        self._analog_snr =v

    def set_digital_snr(self,v):
        self._digital_snr =v

    def set_snr(self,var,snr):
        self._snr[var] = snr

    def snr(self,var):
        if var in self._snr:
            return self._snr[var]
        else:
            return self.analog_snr()

    def _compute_order(self):
        self.__order = []
        self.__order_integs = []
        self.__types = {}
        fns = []
        for var in self._variables:
            if not (var in self._bindings):
                continue

            if self._bindings[var].op == op.OpType.INTEG:
                self.__types[var] = MathProg.ExprType.INTEG
                self.__order.append(var)
                self.__order_integs.append(var)
            elif self._bindings[var].op == op.OpType.EXTVAR:
                self.__types[var] = MathProg.ExprType.EXTERN
                self.__order.append(var)

            else:
                self.__types[var] = MathProg.ExprType.FN
                fns.append(var)

        while not util.values_in_list(fns,self.__order):
            progress = False
            for var in fns:
                variables = self._bindings[var].vars()
                if util.values_in_list(variables,self.__order):
                    self.__order.append(var)
                    progress = True
            assert(progress)


    def _curr_state_map(self,menv,t,stvals):
        stdict = dict(zip(self.__order_integs,stvals))
        for var in self.__order:
            typ = self.__types[var]
            if typ == MathProg.ExprType.EXTERN:
                extvar = self._bindings[var].name
                stdict[var] = menv.input(extvar).compute({'t':t})
            elif typ == MathProg.ExprType.FN:
                stdict[var] = self._bindings[var].compute(stdict)
            elif typ == MathProg.ExprType.INTEG:
                continue
            else:
                raise Exception("unknown: %s" % var)

        return stdict

    @property
    def variable_order(self):
        return self.__order

    def curr_state(self,menv,t,stvals):
        m = self._curr_state_map(menv,t,stvals)
        return list(map(lambda var: m[var], self.__order))

    def next_deriv(self,menv,t,stvals):
        stdict = self._curr_state_map(menv,t,stvals)
        derivs = {}
        for var in self.__order_integs:
            derivs[var] = self._bindings[var].deriv.compute(stdict)

        deriv_list = list(map(lambda q: derivs[q],self.__order_integs))
        return deriv_list

    def init_state(self,menv):
        ics = {}
        for var in self.__order:
            typ = self.__types[var]
            if typ == MathProg.ExprType.INTEG:
                ics[var] = self._bindings[var].init_cond.value
            elif typ == MathProg.ExprType.EXTERN:
                extvar = self._bindings[var].name
                ics[var] = menv.input(extvar).compute({'t':0})
            elif typ == MathProg.ExprType.EXTERN:
                ics[var] = self._binding[var].compute(ics)


        return list(map(lambda q: ics[q],self.__order_integs))

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
        bw = self._bandwidths[v]
        assert(isinstance(bw,Bandwidth))
        return bw

    def set_max_sim_time(self,t):
        self.max_sim_time = t

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

                icoll = expr.compute_interval(self._intervals)
                self._intervals[variable] = icoll.interval


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
                        all_bound = all(map(lambda v: v in self._intervals, \
                                            expr.handles() + expr.vars()))
                        if not all_bound:
                            new_ivals = expr.infer_interval(self._intervals[variable], \
                                                            self._intervals)
                            ival_dict = new_ivals.merge_dict(self._intervals).dict()
                        else:
                            ival_dict = self._intervals

                        bwcoll = expr.infer_bandwidth(ival_dict, \
                                                      bandwidths=self._bandwidths)
                        assert(isinstance(bwcoll.bandwidth, Bandwidth))
                        self._bandwidths[variable] = bwcoll.bandwidth
                        progress = True

        if not (util.keys_in_dict(self._bindings.keys(), self._bandwidths)):
            for k in self._bindings.keys():
                if not k in self._bandwidths:
                    print("  :no bw %s" % k)
                else:
                    print("  :bw %s" % k)
            raise Exception("can't compile %s: missing bandwidths" % self.name)

        if not (util.keys_in_dict(self._bindings.keys(), self._intervals)):
            for k in self._bindings.keys():
                if not k in self._intervals:
                    print("  :no ival %s" % k)
                else:
                    print("  :ival %s" % k)
            raise Exception("can't compile %s: missing intervals" % self.name)


        self._compute_order()

    @property
    def name(self):
        return self._name

    def __repr__(self):
        s = "prog %s\n" % self._name
        for v,e in self._bindings.items():
            s += "  %s=%s\n" % (v,e)
        s += "\n"
        for v,b in self._bandwidths.items():
            s += "  bw %s=%s\n" % (v,b)
        s += "\n"
        for v,i in self._intervals.items():
            s += "  iv %s=%s\n" % (v,i)


        return s
