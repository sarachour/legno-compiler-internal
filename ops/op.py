import itertools
import math
import ops.interval as interval

class Op:
    EQ = 0
    MULT = 1
    INTEG = 2
    ADD = 3
    EXP = 4
    LN = 5
    SQRT = 6
    SQUARE = 7
    CONST = 8
    VAR = 9
    POW = 10
    EMIT = 11
    EXTVAR = 12
    STRMAP = {
        EQ: "=",
        MULT: "*",
        INTEG: "int",
        ADD: "+",
        EXP: "exp",
        SQRT: "sqrt",
        LN: "ln",
        SQUARE: "pow2",
        CONST: "const",
        VAR: "var",
        POW: "pow",
        EMIT: "emit",
        EXTVAR: "extvar"
    }

    def __init__(self,op,args):
        for arg in args:
            assert(isinstance(arg,Op))
        self._args = args
        self._op = op
        self._is_associative = True \
                               if op in [Op.MULT, Op.ADD] \
                                  else False

    @property
    def op(self):
        return self._op

    @property
    def state_vars(self):
        stvars = {}
        for substvars in self._args():
            for k,v in substvars.items():
                assert(not k in stvars)
                stvars[k] =v
        return stvars

    def handles(self):
        handles = []
        for arg in self._args:
            for handle in arg.handles():
                assert(not handle in handles)
                handles.append(handle)

        return handles

    def toplevel(self):
        return None

    def compute(self,bindings={}):
        raise Exception("compute not implemented: %s" % self)

    def arg(self,idx):
        return self._args[idx]

    @property
    def args(self):
        return self._args

    def nodes(self):
        child_nodes = sum(map(lambda a: a.nodes(), self._args))
        return 1 + child_nodes

    def depth(self):
        if len(self._args) == 0:
            return 0

        child_depth = max(map(lambda a: a.depth(), self._args))
        return 1 + child_depth


    def __repr__(self):
        argstr = " ".join(map(lambda arg: str(arg),self._args))
        return "(%s %s)" % (Op.STRMAP[self._op],argstr)

    def __eq__(self,other):
        assert(isinstance(other,Op))
        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def vars(self):
        vars = []
        for arg in self._args:
            vars += arg.vars()

        return vars

    def match_op(self,expr):
        if expr.op == self._op:
            return True,False,[zip(self._args,expr.args)]

        else:
            return False,False,None

    def bandwidth(self,intervals,bandwidths,bindings):
        raise NotImplementedError("unknown bandwidth <%s>" % (str(self)))

    def match(self,expr):
        def is_consistent(assignments):
            bnds = {}
            for v,e in assignments:
                if not v in bnds:
                    bnds[v] = e
                else:
                    print("%s -> %s :-> %s" % (v,bnds[v],e))
                    raise NotImplementedError

            return True

        can_match,eq_op,bindings = self.match_op(expr)
        if can_match:
            for binding in bindings:
                assigns = []
                submatches = []
                for v,e in binding:
                    if v.op == Op.VAR:
                        assigns.append((v.name,e))
                    else:
                        submatches2 = []
                        for is_subeq, subassigns in v.match(e):
                            submatches3 = list(map(lambda subassign:
                                     (is_subeq,subassign), subassigns))
                            submatches2.append(submatches3)


                        submatches.append(submatches2)


                if not is_consistent(assigns):
                    continue

                for choices in itertools.product(*submatches):
                    combo = []
                    for choice in choices:
                        combo += choice

                    is_eq_match = eq_op and \
                                  all(map(lambda tup: tup[0], combo))
                    assigns2 = list(map(lambda tup: tup[1], combo))
                    if not is_consistent(assigns+assigns2):
                        continue

                    yield is_eq_match,assigns+assigns2
        else:
            return

class Op2(Op):

    def __init__(self,op,args):
        Op.__init__(self,op,args)
        assert(len(args) == 2)

    @property
    def arg1(self):
        return self._args[0]

    @property
    def arg2(self):
        return self._args[1]

    def compute(self,bindings):
        arg1 = self._args[0].compute(bindings)
        arg2 = self._args[1].compute(bindings)
        return self.compute_op2(arg1,arg2)

    def compute_op2(self,arg1,arg2):
        raise Exception("compute_op2 not implemented: %s" % self)

class BaseExpOp(Op):
    def __init__(self,op,args):
        Op2.__init__(self,op,args)

    @property
    def base(self):
        return self._args[0]

    @property
    def exponent(self):
        return self._args[1]


class Integ(Op2):

    def __init__(self,deriv,init_cond,handle=None):
        assert(handle.startswith(":"))

        Op.__init__(self,Op.INTEG,[deriv,init_cond])
        self._handle = handle
        pass

    @property
    def handle(self):
        return self._handle

    @property
    def deriv_handle(self):
        return self._handle+"\'"

    @property
    def init_cond(self):
        return self.arg2

    def handles(self):
        ch = Op.handles(self)
        assert(not self.handle in ch and \
               not self.handle is None)
        ch.append(self.handle)
        ch.append(self.deriv_handle)
        return ch

    def toplevel(self):
        return self.handle

    def interval(self,bindings):
        assert(not self.handle is None)
        assert(not self.deriv_handle is None)
        ideriv = self.deriv.interval(bindings)
        icond = self.init_cond.interval(bindings)
        istvar = icond.interval.union(bindings[self.handle])
        assert(not self.handle is None)
        icomb = icond.merge(ideriv, istvar)
        icomb.bind(self.deriv_handle, ideriv.interval)
        return icomb

    def state_vars(self):
        stvars = Op.state_vars(self)
        stvars[self._handle] = self
        return

    def bandwidth(self,intervals,bandwidths,bindings):
        expr = self.deriv
        min_val,max_val = self.deriv.interval(intervals).interval
        tau,time_su = 1.0,1.0
        # time required to raise 1 unit
        rise_time = (tau*time_su)/(max_val-min_val)
        bandwidth = 0.35/rise_time
        return bandwidth

    @property
    def deriv(self):
        return self.arg1

class Ln(Op):

    def __init__(self,arg):
        Op.__init__(self,Op.LN,[arg])
        pass


class Exp(Op):

    def __init__(self,arg):
        Op.__init__(self,Op.EXP,[arg])
        pass


class Pow(BaseExpOp):

    def __init__(self,arg1,arg2):
        Op.__init__(self,Op.POW,[arg1,arg2])
        pass


class Square(BaseExpOp):

    def __init__(self,arg):
        Op.__init__(self,Op.SQUARE,[arg])
        pass

    def match_op(self,expr, enable_eq=False):
        if expr.op == self._op:
            return True,False,[[(self.base,expr.base)]]

        elif expr.op == Op.POW:
            if expr.exponent.op == Op.CONST and \
               expr.exponent.value == 2.0:
                return True,False,[[(self.base,expr.base)]]

            elif expr.exponent.op == Op.MULT and \
                 expr.arg1 == expr.arg2 and \
                 expr.arg1.op == Op.VAR:
                return True,False,[[(self.base,expr.arg1)]]

        return False,None,None



    @property
    def exponent(self):
        return Const(2)


class ExtVar(Op):

    def __init__(self,name):
        Op.__init__(self,Op.EXTVAR,[])
        self._name = name

    @property
    def name(self):
        return self._name

    def interval(self,bindings):
        return interval.IntervalCollection(bindings[self._name])

    def bandwidth(self,intervals,bandwidths,bindings):
        return bandwidths[self._name]

    @property
    def name(self):
        return self._name

    def __repr__(self):
        return "(%s %s)" % \
            (Op.STRMAP[self._op],self._name)


class Var(Op):

    def __init__(self,name):
        Op.__init__(self,Op.VAR,[])
        self._name = name

    def __repr__(self):
        return "(%s %s)" % \
            (Op.STRMAP[self._op],self._name)

    @property
    def name(self):
        return self._name

    def interval(self,bindings):
        assert(self._name in bindings)
        return interval.IntervalCollection(bindings[self._name])

    def bandwidth(self,intervals,bandwidths,bindings):
        new_b = dict(filter(lambda el: el[0] != self._name, bindings.items()))
        return bindings[self._name].bandwidth(intervals,bandwidths,new_b)

    def compute(self,bindings):
        if not self._name in bindings:
            for key in bindings:
                print(key)
            raise Exception("<%s> not bound" % self._name)

        return bindings[self._name]

    def match_op(self,expr):
        return True,True,[[(self,expr)]]


    def vars(self):
        return [self._name]

class Const(Op):

    def __init__(self,value):
        Op.__init__(self,Op.CONST,[])
        self._value = value


    def compute(self,bindings):
        return self._value

    def interval(self,bindings):
        return interval.IntervalCollection(
            interval.IValue(self._value)
        )

    def bandwidth(self,intervals,bandwidths,bindings):
        return 0.0

    @property
    def value(self):
        return self._value

    def match_op(self,expr):
        if expr.op == self.op and \
           expr.value == self.value:
            return True,True,[]

        else:
            return False,None,None

    def __repr__(self):
        return "(%s %s)" % \
            (Op.STRMAP[self._op],self._value)



class Sqrt(BaseExpOp):

    def __init__(self,arg):
        Op.__init__(self,Op.SQRT,[arg])
        pass


    def match_op(self,expr,enable_eq=False):
        if expr.op == self._op:
            return True,False,[[self.base,expr.base]]

        elif expr.op == Op.POW:
            if expr.exponent.op == Op.CONST and \
               expr.exponent.value == 0.5:
                return True,False,[[self.base,expr.base]]

        return False,False,None


    @property
    def exponent(self):
        return Const(0.5)



class Emit(Op):

    def __init__(self,node):
        Op.__init__(self,Op.EMIT,[node])
        pass

    def bandwidth(self,intervals,bandwidths,bindings):
        return self.arg(0).bandwidth(intervals,bandwidths,bindings)

    def interval(self,bindings):
        return self.arg(0).interval(bindings)


    def compute(self,bindings):
        return self.arg(0).compute(bindings)


class Mult(Op2):

    def __init__(self,arg1,arg2):
        Op2.__init__(self,Op.MULT,[arg1,arg2])
        pass


    def interval(self,bindings):
        is1 = self.arg1.interval(bindings)
        is2 = self.arg2.interval(bindings)
        return is1.merge(is2,
                  is1.interval.mult(is2.interval))

    def bandwidth(self,intervals,bandwidths,bindings):
        if self.arg1.op == Op.CONST:
            value = abs(self.arg1.value)
            f2 = self.arg2.bandwidth(intervals,bandwidths,bindings)
            return f2*value

        elif self.arg2.op == Op.CONST:
            value = abs(self.arg2.value)
            f2 = self.arg1.bandwidth(intervals,bandwidths,bindings)
            return f2*value

        else:
            raise Exception("cannot compute bandwidth of nonlinear fxn: <%s>" % self)

    def match_op(self,expr):
        if expr.op == self._op:
            return True,False,[
                [(self.arg1,expr.arg1),(self.arg2,expr.arg2)],
                [(self.arg1,expr.arg2),(self.arg2,expr.arg1)]
            ]

        elif expr.op == Op.SQUARE:
            return True,False,[
                [(self.arg1,expr.base),(self.arg2,expr.base)]
            ]

        else:
            return True,True,[
                [(self.arg1,expr),(self.arg2,Const(1))],
                [(self.arg1,Const(1)),(self.arg2,expr)]
            ]


    def compute_op2(self,arg1,arg2):
        return arg1*arg2


class Add(Op2):

    def __init__(self,arg1,arg2):
        Op.__init__(self,Op.ADD,[arg1,arg2])
        pass

    def interval(self,bindings):
        is1 = self.arg1.interval(bindings)
        is2 = self.arg2.interval(bindings)
        return is1.merge(is2,
                  is1.interval.add(is2.interval))


    def bandwidth(self,intervals,bandwidths,bindings):
        bandwidth1 = self.arg1.bandwidth(intervals,bandwidths,bindings)
        bandwidth2 = self.arg2.bandwidth(intervals,bandwidths,bindings)
        return max(bandwidth1,bandwidth2)

    def match_op(self,expr,enable_eq=False):
        if expr.op == self._op:
            return True,False,[
                [(self.arg1,expr.arg1),(self.arg2,expr.arg2)],
                [(self.arg1,expr.arg2),(self.arg2,expr.arg1)]
            ]

        else:
            return True,True,[
                [(self.arg1,expr),(self.arg2,Const(0))],
                [(self.arg1,Const(0)),(self.arg2,expr)]
            ]

    def compute_op2(self,arg1,arg2):
        return arg1+arg2




EQ = Op.EQ
MULT = Op.MULT
INTEG = Op.INTEG
LN = Op.LN
SQRT = Op.SQRT
SQUARE = Op.SQUARE
EXP = Op.EXP
