from enum import Enum
import ops.interval as interval
import math

class NOpType(Enum):
  SIG = "sig"
  SEL = "sel"
  FREQ = "freq"
  CONST_RV = "crv"
  ADD = "+"
  MULT = "*"
  REF = "ref"

class NOp:
    def __init__(self,op,args):
      assert(isinstance(op,NOpType))
      self._args = args
      self._op = op


    def sum_hash(self):
      raise Exception("no sum_hash: %s" % self)

    def mult_hash(self):
      raise Exception("no mult_hash: %s" % self)

    def is_zero(self):
      return False

    def coeff(self):
      raise NotImplementedError

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
      elif op == NOpType.ADD:
        return NAdd.from_json(obj)
      elif op == NOpType.MULT:
        return NMult.from_json(obj)
      elif op == NOpType.SEL:
        return NSelect.from_json(obj)
      elif op == NOpType.REF:
        return NRef.from_json(obj)
      else:
        raise Exception("unknown: %s" % obj)

    def compute(self,freqs,intervals,integral=False):
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


  def terms(self):
    yield self

  def coeff(self):
    return 1.0,0.0

  def mult_hash(self):
    return "%s.%s" % (self.op.value,
                      self._label())

  def sum_hash(self):
    return "%s.%s^%f" % (self.op.value,
                         self._label(),
                         self._power)

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

  def add_like_term(self,rv):
    return mkmult([rv,self])

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

  def _label(self):
    block,loc = self.instance
    if block is None or loc is None:
      label = self._port
    else:
      label = "%s[%s].%s" % (block,loc,self._port)
    return label

  def __repr__(self):
    label = self._label()
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

  def compute(self,freqs,intervals,integral=False):
    if self._value is None:
      raise Exception("[error] cannot directly compute ref.")
    else:
      assert(self.power == 1.0)
      return self._value.compute(freqs,intervals,integral)

  def copy(self):
    return NVar.copy(self,NRef(self._port))

  def mean(self):
    return self.copy()

  def variance(self):
    return mkzero()

  @staticmethod
  def from_json(obj):
    return NRef(obj['port'],
                 obj['block'],
                 obj['loc'])


class NFreq(NVar):

  def __init__(self,port,power=1.0,block=None,loc=None):
    NVar.__init__(self,NOpType.FREQ,port,power,block,loc)

  def compute(self,freqs,intervals,integral=False):
    block,loc = self.instance
    if block is None or loc is None:
      label = self._port
    else:
      label = (block,loc,self._port)

    if not label in freqs:
      raise Exception("not bound: %s, %s" % (label,freqs.keys()))

    if not integral:
      value = freqs[label].bandwidth**self.power
      return interval.Interval.type_infer(0.0, \
                                          value)
    else:
      diff = freqs[label].upper-freqs[label].lower
      if diff == 0.0:
        return interval.Interval.type_infer(0.0,0.0)
      else:
        value = diff**(self.power+1.0)*1/(self.power+1.0)
        return interval.Interval.type_infer(0.0,value)

  def copy(self):
    return NVar.copy(self,NFreq(self._port))

  def mean(self):
    return self.copy()

  def variance(self):
    return mkzero()

  @staticmethod
  def from_json(obj):
    return NFreq(obj['port'],
                 obj['power'],
                 obj['block'],
                 obj['loc'])


class NSig(NVar):

  def __init__(self,port,power=1.0,block=None,loc=None):
    NVar.__init__(self,NOpType.SIG,port,power,block,loc)

  def compute(self,freqs,intervals,integral=False):
    block,loc = self.instance
    if block is None or loc is None:
      label = self._port
    else:
      label = (block,loc,self._port)

    if not label in intervals:
      raise Exception("unbound interval: %s" % label)

    ival = intervals[label]
    return ival.power(self.power)

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
    return mkzero()


class NConstRV(NOp):

  def __init__(self,mu,sigma):
    NOp.__init__(self,NOpType.CONST_RV,[])
    assert(isinstance(sigma,float) or isinstance(sigma,int))
    assert(isinstance(mu,float) or isinstance(mu,int))
    # standard deviation
    self._sigma = sigma
    self._mu = mu

  def is_posynomial(self):
    return self._mu-self._sigma >= 0.0

  def add_like_term(self,rv):
    return NConstRV(self.mu + rv.mu,
                    math.sqrt(self.sigma**2 + rv.sigma**2))

  def sum_hash(self):
    return None

  def coeff(self):
    return self._mu,self._sigma

  def terms(self):
    yield self

  @property
  def mu(self):
    return self._mu

  @property
  def sigma(self):
    return self._sigma

  def is_zero(self):
    return self._sigma == 0.0 and self._mu == 0.0

  def is_constant(self,v):
    return self._sigma == 0.0 and self._mu == v

  def is_one(self):
    return self.is_constant(1.0)

  def variance(self):
    return NConstRV(self._sigma**2,0)

  def mean(self):
    return NConstRV(self._mu,0)

  def sqrt(self):
    if self._sigma == 0.0:
      return NConstRV(self._mu**0.5,0.0)
    else:
      return NConstRV(self._mu**0.5,0.5*self._mu**(-0.5)*self._sigma)

  def square(self):
    return NConstRV(self._mu**2,2*self._sigma*self._mu)

  def mult(self,other):
    assert(other.op == NOpType.CONST_RV)
    mu = self.mu*other.mu
    cov = 0.0
    # cov = 2.0*self.std*other.std
    var = (self.mu**2)*(other.sigma**2) + \
          (other.mu**2)*(self.sigma**2)
    var += cov
    return NConstRV(mu,math.sqrt(var))

  def compute(self,freqs,intervals,integral=False):
    return interval.Interval.type_infer(self.mu-self.sigma*3,\
                                        self.mu+self.sigma*3)


  def __repr__(self):
    return "rv(%.3e,%.3e)" % \
      (self.mu,self.sigma)

  def to_json(self):
    return {
      'op': self.op.value,
      'sigma': self._sigma,
      'mu': self._mu
    }

  @staticmethod
  def from_json(obj):
    return NConstRV(float(obj['mu']), \
                    float(obj['sigma']))



class NMult(NOp):

  def __init__(self,args):
    assert(len(args) > 1)
    for arg in args:
      assert(arg.op != NOpType.ADD and \
             arg.op != NOpType.MULT)

    NOp.__init__(self,NOpType.MULT,args)

  def terms(self):
    for arg in self._args:
      if arg.op == NOpType.MULT:
        for term in arg.terms():
          yield term
      else:
        yield arg

  def add_like_term(self,rv):
    assert(rv.op == NOpType.CONST_RV)
    new_terms = []
    found_rv = False
    for term in self.terms():
      if term.op == NOpType.CONST_RV:
        found_rv = True
        new_terms.append(term.add_like_term(rv))
      else:
        new_terms.append(term.copy())

    if not found_rv:
      new_terms.append(rv.copy())

    return NMult(new_terms)

  def compute(self,freqs,intervals,integral=False):
    result = interval.Interval.type_infer(1.0,1.0)
    for arg in self.args():
      result = result.mult(arg.compute(freqs,intervals,integral))
    return result


  def coeff(self):
    rv = mkone()
    for arg in self.args():
      cmu,cstd = arg.coeff()
      rv = rv.mult(NConstRV(cmu,cstd))

    return rv.mu, rv.sigma

  def sum_hash(self):
    hashes = list(filter(lambda h: not h is None,
                         map(lambda a: a.sum_hash(), \
                             self.args())))
    hashes.sort()
    return "|".join(hashes)

  def nonzero(self,args):
    return list(filter(lambda var: not var.zero(), \
                       args))

  def variance(self):
    means = []
    variance = None
    for arg in self.args():
      var,mean = arg.variance(),arg.mean()
      if var.is_zero() and mean.is_zero():
        return mkzero()
      elif var.is_zero() and not mean.is_zero():
        means.append(mean)
      elif not var.is_zero() and mean.is_zero():
        assert(variance is None)
        variance = var

    if variance is None:
      return mkzero()
    else:
      return NMult(means + [variance])


  def mean(self):
    means = []
    for arg in self.args():
      mean = arg.mean()
      if mean.is_zero():
        return mkzero()
      means.append(mean)

    return NMult(means)

  def square(self):
    return NMult(list(map(lambda arg: arg.square(), self.args())))


  def sqrt(self):
    return NMult(list(map(lambda arg: arg.sqrt(), self.args())))

  @staticmethod
  def from_json(obj):
    args = []
    for arg in obj['args']:
      node = NOp.from_json(arg)
      args.append(node)

    return NMult(args)



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

  def compute(self,freqs,intervals,integral=False):
    values = list(map(lambda arg: \
                      arg.compute(freqs,intervals,integral),
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

  def compute(self,freqs,intervals,integral=False):
    result = interval.Interval.type_infer(0,0)
    for arg in self.args():
      result = result.add(arg.compute(freqs,intervals,integral=integral))

    return result

  # upper bound
  def square(self):
    # square(a+b) < sqrt(a) + sqrt(b)
    terms = []
    for arg1 in self.args():
      for arg2 in self.args():
        if arg1 == arg2:
          terms.append(arg1.square())
        else:
          terms.append(mkmult([arg1,arg2]))

    return mkadd(terms)


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
      if not variance.is_zero():
        variances.append(variance)

    return mkadd(variances)


  def mean(self):
    means = []
    for arg in self.args():
      mean = arg.mean()
      if not mean.is_zero():
        means.append(mean)

    return mkadd(means)

  @staticmethod
  def from_json(obj):
    args = []
    for arg in obj['args']:
      node = NOp.from_json(arg)
      args.append(node)

    return NAdd(args)

def mksel(args):
  new_args = []
  for arg in args:
    if arg.op == NOpType.SEL:
      for term in arg.terms():
        new_args.append(term)
    elif arg.is_zero():
      continue
    else:
      new_args.append(arg)

  if len(new_args) == 0:
    return mkzero()
  elif len(new_args) == 1:
    return new_args[0]
  else:
    return NSelect(new_args)


def _construct_const_rv(ctor,coeffs):
  if len(coeffs) == 0:
    rv = NConstRV(0.0,0.0)
  elif len(coeffs) == 1:
    rv = coeffs[0]
  else:
    mu,std = ctor(coeffs).coeff()
    rv = NConstRV(mu,std)
  return rv

def _wrap_add(consts,args):
  rv = _construct_const_rv(NAdd,consts)
  if len(args) == 0 and rv.is_zero():
    return mkzero()
  elif len(args) == 0 and not rv.is_zero():
    return rv
  elif rv.is_zero() and len(args) == 1:
    return args[0]
  elif rv.is_zero() and len(args) > 1:
    return NAdd(args)
  else:
    return NAdd([rv] + args)

def _wrap_mult(consts,args,use_mkmult=False):
  rv = _construct_const_rv(NMult,consts)
  if rv.is_zero():
    return mkzero()

  if len(args) == 0:
    return rv

  elif not rv.is_one():
    if use_mkmult:
      return mkmult([rv]+args)
    else:
      return NMult([rv]+args)

  elif rv.is_one() and len(args) == 1:
    return args[0]

def mkzero():
  return NConstRV(0.0,0.0)

def mkconst(c):
  return NConstRV(c,0.0)


def mkone():
  return mkconst(1.0)


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


def mkmult(args):
  sums = []
  terms = []
  expos = {}
  coeffs = [mkone()]

  def add_term(term):
    if term.op == NOpType.CONST_RV:
      coeffs.append(term)

    else:
      hashv = term.mult_hash()
      if not hashv in expos:
        expos[hashv] = 1.0
        terms.append(term)

      expos[hashv] += term.power

  for arg in args:
    if not (arg.is_posynomial()):
      raise Exception("mkmult: term not posy: %s" % arg)

    if arg.op == NOpType.ADD:
      sums.append(arg)
    elif arg.op == NOpType.MULT:
      for term in arg.terms():
        add_term(term)
    elif arg.is_zero():
      return mkzero()
    else:
      add_term(arg)

  expr = _wrap_mult(coeffs,terms)
  if len(sums) > 0:
    expr_terms= list(expr.terms())
    result = distribute(sums,coeff=expr_terms)
  else:
    result = expr

  assert(result.is_posynomial())
  #print("mkmult OLD:%s\n\nNEW:%s\n\n" % (args,result))
  #input()
  return result

def mkadd(args):
  terms = []
  coeffs = {}
  def add_term(term):
    if term.is_zero():
      return
    else:
      hashv = term.sum_hash()
      if not hashv in coeffs:
        terms.append(term)
        coeffs[hashv] = {'mu':0.0,'std':0.0}
      else:
        mu,std = term.coeff()
        coeffs[hashv]['mu'] += mu
        coeffs[hashv]['std'] += std


  for arg in args:
    assert(arg.is_posynomial())
    if arg.op == NOpType.ADD:
      for term in arg.terms():
        add_term(term)
    else:
      add_term(arg)

  final_terms = []
  for term in terms:
    hashv = term.sum_hash()
    mu,std = coeffs[hashv]['mu'],coeffs[hashv]['std']
    final_terms += [term.add_like_term(NConstRV(mu,std))]

  result = _wrap_add([],final_terms)
  assert(result.is_posynomial())
  #print("mkadd OLD:%s\n\nNEW:%s\n\n" % (args,result))
  #input()
  return result
