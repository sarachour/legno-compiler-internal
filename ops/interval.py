
class Interval:

    def __init__(self,lb,ub):
        self._lower = lb
        self._upper = ub


    def union(self,i2):
      lb = min(self.lower,i2.lower)
      ub = max(self.upper,i2.upper)
      return Interval.type_infer(lb,ub)

    @property
    def lower(self):
        return self._lower

    @property
    def upper(self):
        return self._upper

    @staticmethod
    def type_infer(lb,ub):
      if abs(lb - ub) < 1e-6:
        return IValue(lb)
      else:
        return IRange(lb,ub)

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
