from ops.interval import Interval
from ops.bandwidth import Bandwidth, BandwidthCollection
import util.util as util
import sys
from enum import Enum
import ops.op as op

class DSProgDatabase:
    PROGRAMS = {}

    @staticmethod
    def register(name,dsprog,dssim):
        assert(not name in DSProgDatabase.PROGRAMS)
        DSProgDatabase.PROGRAMS[name] = (dsprog,dssim)

    @staticmethod
    def get(name):
        return DSProgDatabase.PROGRAMS[name]

    @staticmethod
    def execute(name):
        prog,sim = DSProgDatabase.get(name)
        plot_diffeq(sim(), \
                    prog())

    def name(self):
        return NotImplementedError

class DSProg:
    class ExprType(Enum):
        INTEG = "integ"
        EXTERN = "extern"
        FN = "fn"

    def __init__(self,name):
        self._name = name
        self._bindings = {}
        self._lambdas = {}
        self._intervals = {}
        self._bandwidths= {}
        self._variables = []
        self._max_sim_time = 1.0

        self.__order = None
        self.__order_integs = None
        self.__types = None
        self.__handles = 0



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


    def build_ode_prob(self):
        ics = {}
        fns = {}
        derivs = {}
        deriv_vars = []
        fn_vars = []
        for var in self.__order:
            typ = self.__types[var]
            if typ == MathProg.ExprType.INTEG:
                _,ics[var] = op.to_python(self._bindings[var].init_cond)
                _,derivs[var] = op.to_python(self._bindings[var].deriv)
                deriv_vars.append(var)
            else:
                _,fns[var] = op.to_python(self._bindings[var])
                fn_vars.append(var)
        return deriv_vars,ics,derivs, \
            fn_vars,fns


    def variables(self):
        return self._variables


    def _bind(self,var,expr):
        assert(not var in self._bindings)
        self._variables.append(var)
        self._bindings[var] = expr

    def decl_stvar(self,var,deriv,ic="0.0",params={}):
        deriv = opparse.parse(deriv.format(**params))
        ic = opparse.parse(params['ic'].format(**params))
        handle = ":h%d" % self.__handles
        expr = op.Integ(deriv,ic,handle=handle)
        self.__handles += 1
        self._bind(var,obj)

    def decl_var(self,var,expr,params={}):
        expr_conc = expr.format(**params)
        return opparse.parse(expr_conc)

    def decl_lambda(self,var,expr,params={}):
        expr_conc = opparse.parse(expr.format(**params))
        self._lambdas[var] = expr_conc

    def bindings(self):
        for var,expr in self._bindings.items():
            yield var,expr

    def binding(self,v):
        if not v in self._bindings:
            return None
        return self._bindings[v]

    def get_interval(self,v):
        return self._intervals[v]

    def interval(self,v,min_v,max_v):
        assert(min_v <= max_v)
        if not v in self._variables:
            self._variables.append(v)
        self._intervals[v] = Interval.type_infer(min_v,max_v)

    def intervals(self):
        for v,ival in self._intervals.items():
            yield v,ival

    def get_bandwidth(self,v):
        bw = self._bandwidths[v]
        assert(isinstance(bw,Bandwidth))
        return bw

    def bandwidth(self,v,b):
        if not v in self._variables:
            self._variables.append(v)
        self._bandwidths[v] = Bandwidth(b)

    def bandwidths(self):
        for v,bw in self._bandwidths.items():
            yield v,bw

    def check(self):
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
