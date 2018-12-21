
class AOp:
    SUM = 0;
    LN = 1;
    EXP = 2;
    INV = 3;
    VPROD = 4;
    CPROD = 5;
    VAR = 6;
    CONST = 7;
    SQUARE = 8;
    SQRT = 9;
    INTEG = 10;
    EMIT = 11;

    TOSTR = {
        SUM: "+",
        LN: "ln",
        EXP: "exp",
        INV: "inv",
        VPROD: "*",
        CPROD: ".*",
        VAR: "v",
        CONST: "c",
        SQUARE: "sq",
        SQRT: "sqrt",
        INTEG: "integ",
        EMIT: "emit"
    }

    def __init__(self,op,inps):
        for inp in inps:
            assert(isinstance(inp,AOp))

        self._inputs = inps
        self._op = op

    @property
    def inputs(self):
        return self._inputs

    def input(self,v):
        return self._inputs[v]

    @property
    def op(self):
        return self._op

    def vars(self):
        vars = []
        for inp in self.inputs:
            vars += inp.vars()
        return vars

    def make(self,ctor,inputs):
        return ctor(inputs)

    def label(self):
        return AOp.TOSTR[self.op]

    def tostr(self,delim='\n',indent='   ',prefix=''):
        argstr = ""
        for inp in self._inputs:
            inp.tostr(delim=delim,indent=indent,prefix=prefix+indent)
        return prefix+self.label()+delim+argstr

    def __repr__(self):
        argstr = " ".join(map(lambda x: str(x), self._inputs))
        return "(%s %s)" % (self.label(),argstr)

class AVar(AOp):

    def __init__(self,var):
        AOp.__init__(self,AOp.VAR,[])
        self._var = var

    def make(self,inputs):
        return AVar(self._var)

    @property
    def name(self):
        return self._var

    def vars(self):
        return [self._var]

    def label(self):
        return str(self._var)

class AConst(AOp):

    def __init__(self):
        AOp.__init__(self,AOp.CONST,[])

    def make(self,inputs):
        return AConst()


    def label(self):
        return str("<#>")


class AGain(AOp):

    def __init__(self,value,expr):
        AOp.__init__(self,AOp.CPROD, [expr])
        assert(isinstance(expr,AOp))
        assert(isinstance(value,float) or \
               isinstance(value,int))
        self._value = value

    @property
    def input(self):
        return self._inputs[0]

    def make(self,inputs):
        return AGain(self._value,inputs[0])

    @property
    def value(self):
        return self._value

    def label(self):
        return AOp.TOSTR[self.op] + ":"+ str(self._value)

class AProd(AOp):

    def __init__(self,inputs):
        AOp.__init__(self,AOp.VPROD,inputs)

    def make(self,inputs):
        return AProd(inputs)


class ASum(AOp):

    def __init__(self,inputs):
        AOp.__init__(self,AOp.SUM,inputs)


    def make(self,inputs):
        return ASum(inputs)


class AInteg(AOp):

    def __init__(self,expr,ic):
        AOp.__init__(self,AOp.INTEG,[expr,ic])

    def make(self,inputs):
        return AInteg(inputs[0],inputs[1])


class AFunc(AOp):

    def __init__(self,kind,inputs):
        AOp.__init__(self,kind,inputs)

    def make(self,inputs):
        return AFunc(self._op,inputs)


