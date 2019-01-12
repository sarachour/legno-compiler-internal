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
        return "(var %s)" % self._name


class JConst(JOp):

    def __init__(self,value):
        JOp.__init__(self,JOpType.CONST,[])
        self._value = value


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
        return c1*c2,JMult(x1,x2)


