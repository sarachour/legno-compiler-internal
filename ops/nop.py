from enum import Enum
import ops.interval as interval

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

    def args(self):
      for arg in self._args:
        yield arg

    def square(self):
      raise Exception("square-unimpl: %s" % self)

    def to_json(self):
      args = list(map(lambda arg: arg.to_json(), \
                      self._args))
      return {
        'op': self.op.value,
        'args': args
      }


    @staticmethod
    def from_json(obj):
      op = NOpType(obj['op'])
      if op == NOpType.SIG:
        return NSig.from_json(obj)
      elif op == NOpType.FREQ:
        return NFreq.from_json(obj)
      elif op == NOpType.CONST_RV:
        return NConstRV.from_json(obj)
      elif op == NOpType.CONST_VAL:
        return NConstVal.from_json(obj)
      elif op == NOpType.ADD:
        return NAdd.from_json(obj)
      elif op == NOpType.MULT:
        return NMult.from_json(obj)
      elif op == NOpType.INV:
        return NInv.from_json(obj)
      elif op == NOpType.ZERO:
        return NZero()

    def compute(self,freqs,intervals):
      raise Exception("not-implemented [compute]: %s" % self)

    def square(self):
      return self

    def mean(self):
      raise NotImplementedError

    def variance(self):
      raise NotImplementedError

    @property
    def op(self):
        return self._op

    def __repr__(self):
      delim = self._op.value
      argstr = delim.join(map(lambda x : str(x),self._args))
      return "(%s)" % argstr

class NVar(NOp):

  def __init__(self,op,name,power=1.0):
    self._port = name
    self._power = power
    self._instance = (None,None)
    NOp.__init__(self,op,[])

  def __repr__(self):
    if self._power != 1.0:
      return "%s(%s)^%f" % \
        (self.op.value,self._port,self._power)
    else:
      return "%s(%s)" % (self.op.value,self._port)

  def to_json(self):
    return {
      'op': self.op.value,
      'port':self._port,
      'power': self._power
    }

class NFreq(NVar):

  def __init__(self,port,power=1.0):
    NVar.__init__(self,NOpType.FREQ,port,power)

  def compute(self,freqs,intervals):
    return interval.Interval.type_infer(0.0, \
                  freqs[self._port].bandwidth)

  def mean(self):
    return NFreq(self._port,self._power)

  def square(self):
    return NFreq(self._port,self._power*2)

  def variance(self):
    return NZero()

  @staticmethod
  def from_json(obj):
    return NFreq(obj['port'],obj['power'])


class NSig(NVar):

  def __init__(self,port,power=1.0):
    NVar.__init__(self,NOpType.SIG,port,power)

  def square(self):
    return NSig(self._port,self._power*2)

  def compute(self,freqs,intervals):
    ival = intervals[self._port]
    if ival.lower <= 0.0 and ival.upper >= 0.0:
      return interval.Interval.type_infer(0.0,ival.bound)
    else:
      lower_bnd = min(abs(ival.lower),abs(ival.upper))
      return interval.Interval.type_infer(lower_bnd,ival.bound)

  @staticmethod
  def from_json(obj):
    return NSig(obj['port'],obj['power'])


  def mean(self):
    return NSig(self._port,self._power)

  def variance(self):
    return NZero()




class NConstRV(NOp):

  def __init__(self,sigma):
    NOp.__init__(self,NOpType.CONST_RV,[])
    assert(isinstance(sigma,float))
    # standard deviation
    self._sigma = sigma


  def variance(self):
    return NConstVal(self._sigma**2)

  def mean(self):
    return NZero()

  def compute(self,freqs,intervals):
    return interval.Interval.type_infer(0.0,self._sigma)


  def __repr__(self):
    return "std(%s)" % self._sigma

  def to_json(self):
    return {
      'op': self.op.value,
      'sigma': self._sigma
    }

  @staticmethod
  def from_json(obj):
    return NConstRV(float(obj['sigma']))



class NZero(NOp):

  def __init__(self):
    NOp.__init__(self,NOpType.ZERO,[])

  def variance(self):
    return self

  def mean(self):
    return self

  def __repr__(self):
    return "0"

  def compute(self,freqs,intervals):
    return interval.Interval.type_infer(0.0,0.0)


  @staticmethod
  def from_json(obj):
    return NZero()


class NConstVal(NOp):

  def __init__(self,mu):
    NOp.__init__(self,NOpType.CONST_VAL,[])
    assert(isinstance(mu,float))
    self._mu = mu

  def variance(self):
    return NZero()

  def mean(self):
    return self

  def __repr__(self):
    return "mu(%s)" % (self._mu)

  def to_json(self):
    return {
      'op': self.op.value,
      'mu': self._mu
    }

  def compute(self,freqs,intervals):
    return interval.Interval.type_infer(self._mu,self._mu)


  @staticmethod
  def from_json(obj):
    return NConstVal(float(obj['mu']))


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

  def compute(self,freqs,intervals):
    result = interval.Interval.type_infer(1.0,1.0)
    for arg in self.args():
      result = result.mult(arg.compute(freqs,intervals))
    return result


  def variance(self):
    variances = list(
      filter(
        lambda var: var.op != NOpType.ZERO,
        map(
          lambda arg: arg.variance(),
          self.args()
        )
      )
    )
    means = list(
      filter(
        lambda var: var.op != NOpType.ZERO,
        map(
          lambda arg: arg.mean().square(),
          self.args()
        )
      )
    )

    if len(variances) == 0:
      return NOpType.ZERO
    elif len(variances) == 1:
      return NMult(means + variances)
    else:
      raise Exception("cannot propagate multiple vars: %s" % \
      (self))

  def mean(self):
    return NMult(list(map(lambda arg: arg.mean(), \
                          self.args())))

  @staticmethod
  def from_json(obj):
    args = []
    for arg in obj['args']:
      node = NOp.from_json(arg)
      args.append(node)

    return NMult(args)



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

  def compute(self,freqs,intervals):
    result = interval.Interval.type_infer(0,0)
    for arg in self.args():
      result = result.add(arg.compute(freqs,intervals))

    return result

  def terms(self):
    for arg in self._args:
      if arg.op == NOpType.ADD:
        for term in arg.terms():
          yield term
      else:
        yield arg

  def variance(self):
    return mkadd(list(map(lambda arg: arg.variance(), \
                          self.args())))

  def mean(self):
    return NAdd(list(map(lambda arg: arg.mean(), \
                         self.args())))

  @staticmethod
  def from_json(obj):
    args = []
    for arg in obj['args']:
      node = NOp.from_json(arg)
      args.append(node)

    return NAdd(args)

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
