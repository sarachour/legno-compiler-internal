#TODO: refactor this
#TODO: update gpkit
from enum import Enum

class JOpType(Enum):
    MULT  = "*"
    CONST = "const"
    VAR = "var"

class JOp:

    def __init__(self,op,args):
        assert(isinstance(op,JOpType))
        self._args = args
        self._op = op


    def factor_const(self):
        raise NotImplementedError

    def arg(self,i):
        return self._args[i]

    @property
    def op(self):
        return self._op

    def __repr__(self):
        argstr = " ".join(map(lambda x : str(x),self._args))
        return "(%s %s)" % (self._op.value,argstr)

class JVar(JOp):

    def __init__(self,name,exponent=1.0):
        JOp.__init__(self,JOpType.VAR,[])
        self._name = name
        self._exponent = exponent

    @property
    def exponent(self):
        return self._exponent

    def factor_const(self):
        return 1,self

    @property
    def name(self):
        return self._name

    def __repr__(self):
        if self._exponent == 1.0:
            return "(var %s)" % self._name
        else:
            return "(var %s exp=%f)" % (self._name,self._exponent)

class JConst(JOp):

    def __init__(self,value):
        JOp.__init__(self,JOpType.CONST,[])
        self._value = float(value)


    def factor_const(self):
        return self._value,JConst(1.0)

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return "(const %s)" % self._value

class JMult(JOp):

    def __init__(self,arg1,arg2):
        JOp.__init__(self,JOpType.MULT,[arg1,arg2])

    def factor_const(self):
        c1,x1 = self.arg(0).factor_const()
        c2,x2 = self.arg(1).factor_const()
        c = c1*c2
        if x1.op == JOpType.CONST and x2.op == JOpType.CONST:
            return c, JConst(1.0)
        elif x1.op == JOpType.CONST:
            return c, x2
        elif x2.op == JOpType.CONST:
            return c, x1
        else:
            return c,JMult(x1,x2)



def expo(jexpr, factor):
    if jexpr.op == JOpType.CONST:
        return JConst(jexpr.value**factor)
    elif jexpr.op == JOpType.VAR:
        return JVar(jexpr.name,exponent=jexpr.exponent*factor)
    elif jexpr.op == JOpType.MULT:
        e1 = expo(jexpr.arg(0),factor)
        e2 = expo(jexpr.arg(1),factor)
        return JMult(e1,e2)
    else:
        raise Exception("exponentiate: not-impl %s" % jexpr)

def simplify(jexpr):
    if jexpr.op == JOpType.CONST:
        return JConst(jexpr.value)
    elif jexpr.op == JOpType.VAR:
        return JVar(jexpr.name,jexpr.exponent)
    elif jexpr.op == JOpType.MULT:
        c,e = jexpr.factor_const()
        if c == 1.0:
            return e
        else:
            return JMult(JConst(c),e)
