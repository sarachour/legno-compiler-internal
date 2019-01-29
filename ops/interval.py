
class Interval:

    def __init__(self,lb,ub):
        self._lower = lb
        self._upper = ub


    def union(self,i2):
      lb = min(self.lower,i2.lower)
      ub = max(self.upper,i2.upper)
      return Interval.type_infer(lb,ub)

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
        return num == float('inf') or num == float('-inf')

    @staticmethod
    def type_infer(lb,ub):
      if Interval.isinf(lb) \
         or Interval.isinf(ub):
        return IUnknown()

      elif abs(lb - ub) < 1e-6:
        return IValue(lb)
      else:
        return IRange(lb,ub)

    def contains(self,child):
        if child.lower >= self.lower and \
           child.upper <= self.upper:
            return True
        else:
            return False


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
        return "[%s,%s]" % (self._lower,self._upper)

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

    def __iter__(self):
      yield self.lower


    def __repr__(self):
      return "[%s]" % self._value

class IRange(Interval):

  def __init__(self,min_value,max_value):
    Interval.__init__(self,min_value,max_value)

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
