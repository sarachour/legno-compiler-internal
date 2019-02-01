from enum import Enum
import ops.interval as interval

class NOpType(Enum):
  SIG = "sig"
  SEL = "sel"
  FREQ = "freq"
  CONST_RV = "crv"
  CONST_VAL = "cval"
  ADD = "+"
  MAX = "max"
  MIN = "min"
  MULT = "*"
  INV = "inv"
  ZERO = "0"

class NOp:
    def __init__(self,op,args):
      assert(isinstance(op,NOpType))
      self._args = args
      self._op = op


    def zero(self):
      return False

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

  def sqrt(self):
    return NFreq(self._port,self._power*0.5)

  def variance(self):
    return NZero()

  @staticmethod
  def from_json(obj):
    return NFreq(obj['port'],obj['power'])


class NSig(NVar):

  def __init__(self,port,power=1.0):
    NVar.__init__(self,NOpType.SIG,port,power)

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

  def sqrt(self):
    return NSig(self._port,self._power*0.5)

  def square(self):
    return NSig(self._port,self._power*2)



class NConstRV(NOp):

  def __init__(self,sigma):
    NOp.__init__(self,NOpType.CONST_RV,[])
    assert(isinstance(sigma,float))
    # standard deviation
    self._sigma = sigma

  def zero(self):
    return self._sigma == 0.0

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

  def zero(self):
    return True

  def sqrt(self):
    return self

  def square(self):
    return self

  def variance(self):
    return self

  def mean(self):
    return self

  def __repr__(self):
    return "zero()"

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

  def zero(self):
    return self._mu == 0.0


  def variance(self):
    return NZero()

  def mean(self):
    return self

  def square(self):
    return NConstVal(self._mu**2)

  def sqrt(self):
    return NConstVal(self._mu**0.5)

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


  def nonzero(self,args):
    return list(filter(lambda var: var.op != NOpType.ZERO, \
                       args))

  def variance(self):
    means = []
    variance = None
    for arg in self.args():
      var,mean = arg.variance(),arg.mean()
      if var.zero() and mean.zero():
        return NZero
      elif var.zero() and not mean.zero():
        means.append(mean)
      elif not var.zero() and mean.zero():
        assert(variance is None)
        variance = var

    if variance is None:
      return NZero()
    else:
      return NMult(means + [variance])


  def mean(self):
    means = []
    for arg in self.args():
      mean = arg.mean()
      if mean.zero():
        return NZero()
      means.append(mean)

    return NMult(means)

  def sqrt(self):
    return mkmult(list(map(lambda arg: arg.sqrt(), self.args())))

  @staticmethod
  def from_json(obj):
    args = []
    for arg in obj['args']:
      node = NOp.from_json(arg)
      args.append(node)

    return NMult(args)



  def __init__(self,args):
    assert(len(args) > 1)
    for arg in args:
      assert(arg.op != NOpType.ADD and \
             arg.op != NOpType.MULT)

    NOp.__init__(self,NOpType.MULT,args)

class NSelect(NOp):

  def __init__(self,args):
    assert(len(args) > 1)
    for arg in args:
      assert(arg.op != NOpType.SEL)

    self._args = args
    NOp.__init__(self,NOpType.SEL,args)

  def terms(self):
    for arg in self._args:
      if arg.op == NOpType.SEL:
        for term in arg.terms():
          yield term
      else:
        yield arg


class NAdd(NOp):

  def __init__(self,args):
    assert(len(args) > 1)
    for arg in args:
      assert(arg.op != NOpType.ADD)

    NOp.__init__(self,NOpType.ADD,args)

  def compute(self,freqs,intervals):
    result = interval.Interval.type_infer(0,0)
    for arg in self.args():
      result = result.add(arg.compute(freqs,intervals))

    return result

  # upper bound
  def sqrt(self):
    # sqrt(a+b) < sqrt(a) + sqrt(b)
    return mkadd(list(map(lambda arg: arg.sqrt(), self.args())))

  def terms(self):
    for arg in self._args:
      if arg.op == NOpType.ADD:
        for term in arg.terms():
          yield term
      else:
        yield arg

  def variance(self):
    variances = []
    for arg in self.args():
      variance = arg.variance()
      if not variance.zero():
        variances.append(variance)

    return mkadd(variances)


  def mean(self):
    means = []
    for arg in self.args():
      mean = arg.mean()
      if not mean.zero():
        means.append(mean)

    return mkadd(means)

  @staticmethod
  def from_json(obj):
    args = []
    for arg in obj['args']:
      node = NOp.from_json(arg)
      args.append(node)

    return NAdd(args)

def mkmin(args):
  new_args = []
  for arg in args:
    if arg.op == NOpType.MIN:
      for term in arg.terms():
        new_args.append(term)
    elif arg.op == NOpType.ZERO:
      return NZero()
    else:
      new_args.append(arg)

  if len(new_args) == 0:
    return NZero()
  elif len(new_args) == 1:
    return new_args[0]
  else:
    return NSelect(new_args)


def mksel(args):
  new_args = []
  for arg in args:
    if arg.op == NOpType.SEL:
      for term in arg.terms():
        new_args.append(term)
    elif arg.op == NOpType.ZERO:
      continue
    else:
      new_args.append(arg)

  if len(new_args) == 0:
    return NZero()
  elif len(new_args) == 1:
    return new_args[0]
  else:
    return NSelect(new_args)


def mkadd(args):
  new_args = []
  for arg in args:
    if arg.op == NOpType.ADD:
      for term in arg.terms():
        new_args.append(term)
    elif arg.op == NOpType.ZERO:
      continue
    else:
      new_args.append(arg)

  if len(new_args) == 0:
    return NZero()
  elif len(new_args) == 1:
    return new_args[0]
  else:
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
    elif arg.op == NOpType.ZERO:
      return NZero()
    else:
      coeff.append(arg)

  if len(sums) > 0:
    return NMult.distribute(sums,coeff=coeff)
  else:
    return NMult(coeff)
