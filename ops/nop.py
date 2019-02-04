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
  REF = "ref"

class NOp:
    def __init__(self,op,args):
      assert(isinstance(op,NOpType))
      self._args = args
      self._op = op


    def zero(self):
      return False

    def is_posynomial(self):
      return all(map(lambda arg: arg.is_posynomial(), \
                    self.args()))

    def vars(self):
      allvars = []
      for arg in self.args():
        allvars += arg.vars()
      return set(allvars)

    def arg(self,i):
        return self._args[i]

    def args(self):
      for arg in self._args:
        yield arg

    def sqrt(self):
      raise Exception("sqrt-unimpl: %s" % self)

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
      elif op == NOpType.SEL:
        return NSelect.from_json(obj)
      elif op == NOpType.REF:
        return NRef.from_json(obj)
      else:
        raise Exception("unknown: %s" % obj)

    def compute(self,freqs,intervals):
      raise Exception("not-implemented [compute]: %s" % self)


    def mean(self):
      raise NotImplementedError

    def variance(self):
      raise NotImplementedError

    def concretize(self,ref_dict):
      for arg in self.args():
        arg.concretize(ref_dict)


    def bind_instance(self,block_name,loc):
      for arg in self.args():
        arg.bind_instance(block_name,loc)

    @property
    def op(self):
        return self._op

    def __repr__(self):
      delim = self._op.value
      argstr = delim.join(map(lambda x : str(x),self._args))
      return "(%s)" % argstr

class NVar(NOp):

  def __init__(self,op,name,power=1.0,block=None,loc=None):
    self._port = name
    self._power = power
    self._instance = (block,loc)
    NOp.__init__(self,op,[])


  def is_posynomial(self):
      return True

  @property
  def power(self):
    return self._power

  @property
  def port(self):
    return self._port

  @property
  def instance(self):
    return self._instance

  def bind_instance(self,block_name,loc):
    self._instance = (block_name,loc)

  def copy(self,n):
    n._instance = self._instance
    n._port = self._port
    n._power = self._power
    return n

  def sqrt(self):
    node = self.copy()
    node._power = self._power*0.5
    return node

  def square(self):
    node = self.copy()
    node._power = self._power*2
    return node

  def vars(self):
    return [self]

  def __repr__(self):
    block,loc = self.instance
    if block is None or loc is None:
      label = self._port
    else:
      label = "%s[%s].%s" % (block,loc,self._port)

    if self._power != 1.0:
      return "%s(%s)^%f" % \
        (self.op.value,label,self._power)
    else:
      return "%s(%s)" % (self.op.value,label)

  def to_json(self):
    return {
      'op': self.op.value,
      'port':self._port,
      'block': self._instance[0],
      'loc': self._instance[1],
      'power': self._power
    }

class NRef(NVar):

  def __init__(self,port,block=None,loc=None):
    NVar.__init__(self,NOpType.REF,port,1.0,block,loc)
    self._value = None

  def concretize(self,ref_dict):
    block,loc = self.instance
    if block is None or loc is None:
      key = self.port
    else:
      key = (block,loc,self.port)

    if not key in ref_dict:
      raise Exception("<%s> not in reference map" % (key))

    self._value = ref_dict[key]
    assert(isinstance(self._value, NOp))

  def compute(self,freqs,intervals):
    if self._value is None:
      raise Exception("[error] cannot directly compute ref.")
    else:
      return self._value.compute(freqs,intervals)

  def copy(self):
    return NVar.copy(self,NRef(self._port))

  def mean(self):
    return self.copy()

  def variance(self):
    return NZero()

  @staticmethod
  def from_json(obj):
    return NRef(obj['port'],
                 obj['block'],
                 obj['loc'])


class NFreq(NVar):

  def __init__(self,port,power=1.0,block=None,loc=None):
    NVar.__init__(self,NOpType.FREQ,port,power,block,loc)

  def compute(self,freqs,intervals):
    block,loc = self.instance
    if block is None or loc is None:
      label = self._port
    else:
      label = (block,loc,self._port)

    if not label in freqs:
      raise Exception("not bound: %s, %s" % (label,freqs.keys()))

    return interval.Interval.type_infer(0.0, \
                  freqs[label].bandwidth)

  def copy(self):
    return NVar.copy(self,NFreq(self._port))
  def mean(self):
    return self.copy()

  def variance(self):
    return NZero()

  @staticmethod
  def from_json(obj):
    return NFreq(obj['port'],
                 obj['power'],
                 obj['block'],
                 obj['loc'])


class NSig(NVar):

  def __init__(self,port,power=1.0,block=None,loc=None):
    NVar.__init__(self,NOpType.SIG,port,power,block,loc)

  def compute(self,freqs,intervals):
    block,loc = self.instance
    if block is None or loc is None:
      label = self._port
    else:
      label = (block,loc,self._port)

    if not label in intervals:
      raise Exception("unbound interval: %s" % label)

    ival = intervals[label]
    return ival

  @staticmethod
  def from_json(obj):
    return NSig(obj['port'],
                 obj['power'],
                 obj['block'],
                 obj['loc'])


  def copy(self):
    return NVar.copy(self,NSig(self._port))


  def mean(self):
    return self.copy()

  def variance(self):
    return NZero()


class NConstRV(NOp):

  def __init__(self,sigma):
    NOp.__init__(self,NOpType.CONST_RV,[])
    assert(isinstance(sigma,float))
    # standard deviation
    self._sigma = sigma

  def is_posynomial(self):
      return self._sigma >= 0.0


  @property
  def sigma(self):
    return self._sigma

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

  def is_posynomial(self):
      return True


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
    assert(isinstance(mu,float) or isinstance(mu,int))
    self._mu = mu

  def zero(self):
    return self._mu == 0.0

  @property
  def mu(self):
    return self._mu

  def is_posynomial(self):
      return self._mu >= 0.0


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

  def square(self):
    return mkmult(list(map(lambda arg: arg.square(), self.args())))


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
  class Mode(Enum):
    MAX = "max"
    MIN = "min"
    DIFF = "diff"
    UNKNOWN = "unknown"

  def __init__(self,args):
    assert(len(args) > 1)
    self._mode = NSelect.Mode.UNKNOWN
    for arg in args:
      assert(arg.op != NOpType.SEL)

    self._args = args
    NOp.__init__(self,NOpType.SEL,args)

  def compute_min(self,values):
    result = None
    for value in values:
      if result is None:
        result = value
      elif value.upper < result.upper:
        result = value
      elif value.upper == result.upper and \
           value.lower > result.lower:
        result = value

    return result


  @staticmethod
  def from_json(obj):
    args = []
    for arg in obj['args']:
      node = NOp.from_json(arg)
      args.append(node)

    return NSelect(args)

  def compute_max(self,values):
    result = None
    for value in values:
      if result is None:
        result = value
      elif value.upper > result.upper:
        result = value
      elif value.upper == result.upper and \
           value.lower > result.lower:
        result = value

    return result

  def compute(self,freqs,intervals):
    values = list(map(lambda arg: \
                      arg.compute(freqs,intervals),
                      self.args()))
    if self._mode == NSelect.Mode.MAX:
      return self.compute_max(values)

    elif self._mode == NSelect.Mode.MIN:
      return self.compute_min(values)

    elif self._mode == NSelect.Mode.DIFF:
      loval = self.compute_min(values)
      hival = self.compute_max(values)
      return hival.add(loval.negate())
    else:
      raise Exception("unsupported mode: %s" % self._mode)


  def set_mode(self,mode):
    self._mode = mode

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
  def square(self):
    # sqrt(a+b) < sqrt(a) + sqrt(b)
    return mkadd(list(map(lambda arg: arg.square(), self.args())))


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
