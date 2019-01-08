from enum import Enum

class NOpType(Enum):
  SIG = "sig"
  FREQ = "freq"
  CONST_RV = "crv"
  CONST_VAL = "cval"
  ADD = "+"
  MULT = "*"
  INV = "inv"

class NOp:
    def __init__(self,op,args):
      assert(isinstance(op,NOpType))
      self._args = args
      self._op = op


    def arg(self,i):
        return self._args[i]

    @property
    def op(self):
        return self._op

    def __repr__(self):
        argstr = " ".join(map(lambda x : str(x),self._args))
        return "(%s %s)" % (self._op.value,argstr)

class NFreq(NOp):

  def __init__(self,port):
    NOp.__init__(self,NOpType.FREQ,[])
    self._port port

  def __repr__(self):
    return "freq(%s)" % (self._port)


class NSig(NOp):

  def __init__(self,port):
    NOp.__init__(self,NOpType.SIG,[])
    self._port port

  def __repr__(self):
    return "sig(%s)" % (self._port)


class NConstRV(NOp):

  def __init__(self,sigma):
    NOp.__init__(self,NOpType.CONST_RV,[])
    self._sigma = sigma


  def __repr__(self):
    return "N(0,%s)" % self._sigma


class NConstVal(NOp):

  def __init__(self,mu):
    NOp.__init__(self,NOpType.ADD,[])
    self._mu = mu

  def __repr__(self):
    return "N(%s,0)" % (self._mu)

class NMult(NOp):

  def __init__(self,args):
    for arg in args:
      assert(arg.op != OpType.ADD)

    NOp.__init__(self,NOpType.MULT,args)

class NAdd(NOp):

  def __init__(self,args):
    for arg in args:
      assert(arg.op != OpType.ADD)

    NOp.__init__(self,NOpType.ADD,args)
