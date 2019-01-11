from enum import Enum

class NOpType(Enum):
  SIG = "sig"
  FREQ = "freq"
  CONST_RV = "crv"
  CONST_VAL = "cval"
  ADD = "+"
  MULT = "*"
  INV = "inv"
  ZERO = "0"

class NOp:
    def __init__(self,op,args):
      assert(isinstance(op,NOpType))
      self._args = args
      self._op = op


    def arg(self,i):
        return self._args[i]

    def to_json(self):
      args = list(map(lambda arg: arg.to_json(), \
                      self._args))
      return {
        'op': self.op.name,
        'args': args
      }


    @property
    def op(self):
        return self._op

    def __repr__(self):
      delim = self._op.value
      argstr = delim.join(map(lambda x : str(x),self._args))
      return "(%s)" % argstr

class NFreq(NOp):

  def __init__(self,port):
    NOp.__init__(self,NOpType.FREQ,[])
    self._port = port

  def __repr__(self):
    return "freq(%s)" % (self._port)

  def to_json(self):
    return {
      'op': self.op.name,
      'port': self._port
    }

class NSig(NOp):

  def __init__(self,port):
    NOp.__init__(self,NOpType.SIG,[])
    self._port = port

  def __repr__(self):
    return "val(%s)" % (self._port)

  def to_json(self):
    return {
      'op': self.op.name,
      'port': self._port
    }



class NConstRV(NOp):

  def __init__(self,sigma):
    NOp.__init__(self,NOpType.CONST_RV,[])
    assert(isinstance(sigma,float))
    self._sigma = sigma


  def __repr__(self):
    return "std(%s)" % self._sigma

  def to_json(self):
    return {
      'op': self.op.name,
      'sigma': self._sigma
    }



class NZero(NOp):

  def __init__(self):
    NOp.__init__(self,NOpType.ZERO,[])

  def __repr__(self):
    return "0"

class NConstVal(NOp):

  def __init__(self,mu):
    NOp.__init__(self,NOpType.CONST_VAL,[])
    assert(isinstance(mu,float))
    self._mu = mu

  def __repr__(self):
    return "mu(%s)" % (self._mu)

  def to_json(self):
    return {
      'op': self.op.name,
      'mu': self._mu
    }


class NMult(NOp):

  @staticmethod
  def distribute(sums,coeff=[]):
    state = sums[0]
    for expr in sums[1:]:
      new_terms = []
      for term1 in expr.terms():
        for term2 in state.terms():
          new_terms.append(mkmult([term1,term2]))

      state = NAdd(new_terms)


    new_terms = []
    for term in state.terms():
      new_terms.append(mkmult([term] + coeff))
    state = NAdd(new_terms)

    return state

  def terms(self):
    for arg in self._args:
      if arg.op == NOpType.MULT:
        for term in arg.terms():
          yield term
      else:
        yield arg


  def __init__(self,args):
    for arg in args:
      assert(arg.op != NOpType.ADD and \
             arg.op != NOpType.MULT)

    NOp.__init__(self,NOpType.MULT,args)

class NAdd(NOp):

  def __init__(self,args):
    for arg in args:
      assert(arg.op != NOpType.ADD)

    NOp.__init__(self,NOpType.ADD,args)

  def terms(self):
    for arg in self._args:
      if arg.op == NOpType.ADD:
        for term in arg.terms():
          yield term
      else:
        yield arg

def mkadd(args):
  new_args = []
  for arg in args:
    if arg.op == NOpType.ADD:
      for term in arg.terms():
        new_args.append(term)
    else:
      new_args.append(arg)
  return NAdd(new_args)


def mkmult(args):
  coeff= []
  sums = []
  for arg in args:
    if arg.op == NOpType.ADD:
      sums.append(arg)
    elif arg.op == NOpType.MULT:
      for term in arg.terms():
        coeff.append(term)
    else:
      coeff.append(arg)

  if len(sums) > 0:
    return NMult.distribute(sums,coeff=coeff)
  else:
    return NMult(coeff)
