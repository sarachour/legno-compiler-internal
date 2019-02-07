import math

class Interval:

    def __init__(self,lb,ub):
        self._lower = lb
        self._upper = ub


    def union(self,i2):
      lb = min(self.lower,i2.lower)
      ub = max(self.upper,i2.upper)
      return Interval.type_infer(lb,ub)

    def intersection(self,i2):
        upper = min(i2.upper,self.upper)
        lower = max(i2.lower,self.lower)
        if upper <= lower:
            return Interval.type_infer(0,0)
        else:
            return Interval.type_infer(lower,upper)

    @staticmethod
    def zero():
        return Interval.type_infer(0,0)

    @property
    def spread(self):
        return abs(self.upper-self.lower)

    @property
    def bound(self):
        return max(abs(self.lower),abs(self.upper))

    @property
    def lower(self):
        return self._lower

    @property
    def upper(self):
        return self._upper


    def unbounded(self):
        return Interval.isinf(self.lower) \
            or Interval.isinf(self.upper)

    @staticmethod
    def isinf(num):
        return num == float('inf') \
            or num == float('-inf') \
            or num is None

    @staticmethod
    def type_infer(lb,ub):
      if Interval.isinf(lb) \
         and Interval.isinf(ub):
        return IUnknown()

      elif Interval.isinf(ub):
        assert(not Interval.isinf(lb))
        return ILowerBound(lb)

      elif abs(lb - ub) < 1e-6:
        return IValue(lb)

      else:
        return IRange(lb,ub)

    def contains_value(self,value):
        return value <= self.upper and \
            value >= self.lower

    def contains(self,child):
        if child.lower >= self.lower and \
           child.upper <= self.upper:
            return True
        else:
            return False


    def negate(self):
        return Interval.type_infer(
            -self.upper,
            -self.lower
        )

    def scale(self,v):
        assert(v > 0)
        return Interval.type_infer(
            self.lower*v,
            self.upper*v
        )

    def nonoverlapping(self,i2):
        diff1 = abs(i2.lower - self.lower)
        diff2 = abs(i2.upper - self.upper)
        return max(diff1,diff2)


    def contains_zero(self):
        return self.lower <= 0 or self.upper >= 0


    def crosses_zero(self):
        return self.lower < 0 and self.upper > 0

    def negative(self):
        return self.lower < 0 and self.upper < 0

    def positive(self):
        return self.lower >= 0 and self.upper >= 0

    def sgn(self):
        if self.crosses_zero():
            return Interval.type_infer(-1,1)
        elif self.positive():
            return Interval.type_infer(1,1)
        elif self.negative():
            return Interval.type_infer(-1,-1)


    def abs(self):
        upper = max(abs(self.lower),abs(self.upper))
        lower = min(abs(self.lower),abs(self.upper))
        if self.crosses_zero():
            return Interval.type_infer(0,upper)
        else:
            return Interval.type_infer(lower,upper)

    def sqrt(self):
        assert(not self.crosses_zero())
        assert(not self.negative())
        lower = math.sqrt(self.lower)
        upper = math.sqrt(self.upper)
        return Interval.type_infer(lower,upper)


    def power(self,v):
        if v == 1.0:
            return self
        else:
            print(v)
            raise Exception("?")

    def add(self,i2):
         vals = [
            i2.lower+self.lower,
            i2.upper+self.lower,
            i2.lower+self.upper,
            i2.upper+self.upper
         ]
         lb = min(vals)
         ub = max(vals)
         return Interval.type_infer(lb,ub)


    def mult(self,i2):
        vals = [
            i2.lower*self.lower,
            i2.upper*self.lower,
            i2.lower*self.upper,
            i2.upper*self.upper
        ]
        lb = min(vals)
        ub = max(vals)
        return Interval.type_infer(lb,ub)

    @staticmethod
    def from_json(obj):
        return Interval.type_infer(
            obj['lower'],
            obj['upper']
        )


    def to_json(self):
        return {
            'lower':self.lower,
            'upper':self.upper
        }

    def __repr__(self):
        return "[%.3e,%.3e]" % (self._lower,self._upper)

    def __iter__(self):
        yield self.lower
        yield self.upper

class IValue(Interval):

    def __init__(self,value):
        self._value = value
        Interval.__init__(self,value,value)

    @property
    def value(self):
        return self._value

    def power(self,v):
        return IValue(self.value**v)

    def __iter__(self):
      yield self.lower


    def __repr__(self):
      return "[%.3e]" % self._value

class IRange(Interval):

  def __init__(self,min_value,max_value):
    Interval.__init__(self,min_value,max_value)

class ILowerBound(Interval):

  def __init__(self,min_value):
    Interval.__init__(self,min_value,float('inf'))


class IUnknown(Interval):

  def __init__(self):
    Interval.__init__(self,float('-inf'),float('inf'))

class IntervalCollection:

  def __init__(self,ival):
    if not (isinstance(ival, Interval)):
      raise Exception("not interval: <%s>.T<%s>" % \
                      (ival,ival.__class__.__name__))
    self._ival = ival
    self._bindings = {}

  def update(self,new_ival):
    assert(isinstance(new_ival, Interval))
    self._ival = new_ival

  def bind(self,name,ival):
    assert(isinstance(ival, Interval))
    assert(not name in self._bindings)
    self._bindings[name] = ival

  def bindings(self):
    return self._bindings.items()

  def get(self,name):
      return self._bindings[name]

  @property
  def interval(self):
    return self._ival

  def copy(self):
    ic = IntervalCollection(self.interval)
    for k,v in self.bindings():
      ic.bind(k,v)
    return ic

  def merge(self,other,new_ival):
    new_ivals = self.copy()
    for k,v in other.bindings():
      new_ivals.bind(k,v)

    new_ivals.update(new_ival)
    return new_ivals

  def merge_dict(self,other_dict):
    new_ivals = self.copy()
    for k,v in other_dict.items():
        new_ivals.bind(k,v)

    return new_ivals

  def dict(self):
    return dict(self._bindings)

  def __repr__(self):
    st = "ival %s\n" % self._ival
    for bnd,ival in self._bindings.items():
      st += "  %s: %s\n" % (bnd,ival)

    return st
