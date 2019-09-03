from ops.base_op import *
import math

def to_python(e):
    if e.op == OpType.VAR:
        varname = "%s_" % e.name
        return [varname],varname

    elif e.op == OpType.CONST:
        return [],"%.4e" % e.value

    elif e.op == OpType.ADD:
        vs1,a1 = to_python(e.arg1)
        vs2,a2 = to_python(e.arg2)
        v = list(set(vs1+vs2))
        return v,"(%s)+(%s)" % (a1,a2)


    elif e.op == OpType.POW:
        vs1,a1 = to_python(e.arg(0))
        vs2,a2 = to_python(e.arg(1))
        v = list(set(vs1+vs2))
        return v,"(%s)**(%s)" % (a1,a2)

    elif e.op == OpType.MULT:
        vs1,a1 = to_python(e.arg1)
        vs2,a2 = to_python(e.arg2)
        v = list(set(vs1+vs2))
        return v,"(%s)*(%s)" % (a1,a2)

    elif e.op == OpType.CLAMP:
        v,a = to_python(e.arg1)
        ival = e.interval
        a2 = "max(%f,%s)" % (ival.lower,a)
        a3 = "min(%f,%s)" % (ival.upper,a2)
        return v,a3

    elif e.op == OpType.PAREN:
        v,a = to_python(e.arg(0))
        return v,"(%s)" % a

    elif e.op == OpType.SGN:
        v,a = to_python(e.arg(0))
        return v,"math.copysign(1,%s)" % a

    elif e.op == OpType.RANDFUN:
        v,a = to_python(e.arg(0))
        fmt = "np.interp([{expr}],np.linspace(-1,1,{n}),randlist({seed},{n}))[0]" \
              .format(
                  expr=a,
                  n=e.n,
                  seed=e.seed
              )
        return v,fmt

    elif e.op == OpType.SIN:
        v,a = to_python(e.arg(0))
        return v,"math.sin(%s.real)" % a

    elif e.op == OpType.COS:
        v,a = to_python(e.arg(0))
        return v,"math.cos(%s.real)" % a


    elif e.op == OpType.SQRT:
        v,a = to_python(e.arg(0))
        return v,"math.sqrt(%s)" % a

    elif e.op == OpType.ABS:
        v,a = to_python(e.arg(0))
        return v,"abs(%s)" % a

    elif e.op == OpType.CALL:
        expr = e.func.expr
        args = e.func.func_args
        vals = e.values
        assigns = dict(zip(args,vals))
        conc_expr = expr.substitute(assigns)
        return to_python(conc_expr)

    elif e.op == OpType.EMIT:
        return to_python(e.arg(0))

    else:
        raise Exception("unimpl: %s" % e)


class Func(Op):
    def __init__(self, params, expr):
        Op.__init__(self,OpType.FUNC,[])
        self._expr = expr
        self._vars = params

    def compute(self,bindings):
        for v in self._vars:
            assert(v in bindings)

        return self._expr.compute(bindings)

    @property
    def expr(self):
        return self._expr

    @property
    def func_args(self):
        return self._vars

    def to_json(self):
        obj = Op.to_json(self)
        obj['expr'] = self._expr.to_json()
        obj['vars'] = self._vars
        return obj

    @staticmethod
    def from_json(obj):
        expr = Op.from_json(obj['expr'])
        varnames = obj['vars']
        return Func(list(varnames),expr)

    def apply(self,values):
        assert(len(values) == len(self._vars))
        assigns = dict(zip(self._vars,values))
        return self._expr.substitute(assigns)

    def __repr__(self):
        pars = " ".join(map(lambda p: str(p), self._vars))
        return "lambd(%s).(%s)" % (pars,self._expr)

class Clamp(Op):

    def __init__(self,arg,ival):
        Op.__init__(self,OpType.CLAMP,[arg])
        self._interval = ival

    @property
    def arg1(self):
        return self.arg(0)

    @property
    def interval(self):
        return self._interval

    def compute(self,bindings):
        result = self.arg(0).compute(bindings)
        return self._interval.clamp(result)

    def __repr__(self):
        return "clamp(%s,%s)" % (self.arg(0), \
                              self._interval)

class RandomVar(Op):
    def __init__(self,variance):
        Op.__init__(self,OpType.RANDOM_VAR,[])
        self._variance = variance

    @property
    def variance(self):
        return self._variance

    def compute(self,bindings):
        raise Exception("random variable")


class Abs(Op):

    def __init__(self,arg):
        Op.__init__(self,OpType.ABS,[arg])
        pass

    @staticmethod
    def from_json(obj):
        return Abs(Op.from_json(obj['args'][0]))

    def compute(self,bindings):
        return abs(self.arg(0).compute(bindings))


    def substitute(self,args):
        return Abs(self.arg(0).substitute(args))

    def infer_interval(self,ivals):
        ivalcoll = self.arg(0).infer_interval(ivals)
        ivalcoll.update(ivalcoll.interval.abs())
        return ivalcoll



class RandFun(Op):

    def __init__(self,arg,n=100,seed=None):
        Op.__init__(self,OpType.RANDFUN,[arg])
        self.n = n
        if seed is None:
            self.seed = random.randint(0,1000000)
        else:
            self.seed = seed

    @staticmethod
    def from_json(obj):
        rf = RandFun(Op.from_json(obj['args'][0]), \
                     obj['n'], \
                     obj['seed'])
        return rf

    def substitute(self,assigns):
        rf = RandFun(self.arg(0).substitute(assigns), \
                     self.n,self.seed)
        return rf

    def compute(self,bindings):
        raise NotImplementedError

    def infer_interval(self,ivals):
        ivalcoll = self.arg(0).infer_interval(ivals)
        new_ival = interval.Interval(-1,1)
        ivalcoll.update(new_ival)
        return ivalcoll


    def to_json(self):
        obj = Op.to_json(self)
        obj['n'] = self.n
        obj['seed'] = self.seed
        return obj

class Sgn(Op):

    def __init__(self,arg):
        Op.__init__(self,OpType.SGN,[arg])
        pass

    @staticmethod
    def from_json(obj):
        return Sgn(Op.from_json(obj['args'][0]))

    def substitute(self,assigns):
        return Sgn(self.arg(0).substitute(assigns))

    def compute(self,bindings):
        return math.copysign(1.0,self.arg(0).compute(bindings).real)


    def infer_interval(self,ivals):
        ivalcoll = self.arg(0).infer_interval(ivals)
        new_ival = ivalcoll.interval.sgn()
        ivalcoll.update(new_ival)
        return ivalcoll

class Ln(Op):

    def __init__(self,arg):
        Op.__init__(self,OpType.LN,[arg])
        pass


class Exp(Op):

    def __init__(self,arg):
        Op.__init__(self,OpType.EXP,[arg])
        pass


class Sin(Op):

    def __init__(self,arg1):
        Op.__init__(self,OpType.SIN,[arg1])
        pass

    def compute(self,bindings):
        return math.sin(self.arg(0).compute(bindings).real)


    def substitute(self,args):
        return Sin(self.arg(0).substitute(args))

    @staticmethod
    def from_json(obj):
        return Sin(Op.from_json(obj['args'][0]))

    def infer_interval(self,ivals):
        ivalcoll = self.arg(0).infer_interval(ivals)
        ivalcoll.update(interval.Interval.type_infer(-1,1))
        return ivalcoll

class Cos(Op):

    def __init__(self,arg1):
        Op.__init__(self,OpType.COS,[arg1])
        pass

    def compute(self,bindings):
        return math.cos(self.arg(0).compute(bindings).real)


    @staticmethod
    def from_json(obj):
        return Cos(Op.from_json(obj['args'][0]))


    def substitute(self,args):
        return Cos(self.arg(0).substitute(args))

    def infer_interval(self,ivals):
        ivalcoll = self.arg(0).infer_interval(ivals)
        ivalcoll.update(interval.Interval.type_infer(-1,1))
        return ivalcoll



class UniformNoise(Op):

    def __init__(self,bound,frequency=0.01,period=1.0,seed=5):
        Op.__init__(self,OpType.UNIFNOISE,[])
        self._bound = bound
        self._frequency = frequency
        self._period = period
        self._n = int(self._period/self._frequency)
        np.random.seed(seed)
        self._buf = list(map(lambda i: \
                             np.random.uniform(-self._bound,
                                               self._bound), \
                             range(0,self._n)))

        pass

    @property
    def bound(self):
        return self._bound

    def compute(self,bindings):
        # note: the closer to random noise it is, the harder
        # it is to use a solver
        t = bindings['t']
        i = int((float(t)/self._frequency)) % self._n
        value = self._buf[i]
        return value




class Pow(Op):

    def __init__(self,arg1,arg2):
        Op.__init__(self,OpType.POW,[arg1,arg2])
        pass

    @property
    def arg1(self):
        return self.arg(0)
    @property
    def arg2(self):
        return self.arg(1)

    @staticmethod
    def from_json(obj):
        return Pow(Op.from_json(obj['args'][0]), \
                   Op.from_json(obj['args'][1]))


    def infer_interval(self,ivals):
        bcoll = self.arg(0).compute_interval(ivals)
        ecoll = self.arg(1).compute_interval(ivals)
        new_ival = bcoll.interval.exponent(ecoll.interval)
        rcoll = bcoll.merge(ecoll, new_ival)
        return rcoll

    def substitute(self,args):
        return Pow(
            self.arg(0).substitute(args),
            self.arg(1).substitute(args)
        )


    def compute(self,bindings):
        return self.arg(0).compute(bindings)**self.arg(1).compute(bindings)



class Sqrt(Op):

    def __init__(self,arg):
        Op.__init__(self,OpType.SQRT,[arg])
        pass


    @staticmethod
    def from_json(obj):
        return Sqrt(Op.from_json(obj['args'][0]))


    def compute(self,bindings):
        return math.sqrt(self.arg(0).compute(bindings))

    def infer_interval(self,ivals):
        ivalcoll = self.arg(0).compute_interval(ivals)
        ivalcoll.update(ivalcoll.interval.sqrt())
        return ivalcoll

    @property
    def exponent(self):
        return Const(0.5)

    def substitute(self,args):
        return Sqrt(self.arg(0).substitute(args))

class Square(Op):

    def __init__(self,arg):
        Op.__init__(self,OpType.SQUARE,[arg])
        pass

    @property
    def exponent(self):
        return Const(2)


def Square(a):
    return Mult(a,a)

def Div(a,b):
    return Mult(a,Pow(b,Const(-1)))
