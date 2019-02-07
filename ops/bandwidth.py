import ops.interval as interval
import math

class Bandwidth:

  def __init__(self,bw):
    self._bw = bw

  @property
  def fmax(self):
    return self._bw

  @property
  def bandwidth(self):
    return self._bw

  def add(self,bw2):
    return Bandwidth(max(bw2.bandwidth,self._bw))

  def union(self,bw2):
    return Bandwidth(max(bw2.bandwidth,self._bw))

  def mult(self,bw2):
    return Bandwidth(bw2.bandwidth+self._bw)

  def timescale(self,v):
      assert(v > 0)
      return Bandwidth(
          self._bw*v
      )

  @staticmethod
  def integ(stvar_ival,deriv_ival):
    # each state variable is bandlimited.
    # Bernstein's inequality, Lapidoth, A Foundation in Digital Communication (page 92).
    # given |x(t)| <= A
    # Bernstein's inequality: max(dx/dt) < 2*pi*f_0*A
    # where X(f) = 0 for all f > f_0
    assert(isinstance(deriv_ival, interval.Interval))
    assert(isinstance(stvar_ival, interval.Interval))
    A = stvar_ival.bound
    dA = deriv_ival.bound
    # A = max(f(t)), dA = max(df(t)/dt)
    # dA = 2*pi*f_0*A
    # dA/(2*pi*A) = f_0
    BW = Bandwidth(dA/(2*math.pi*A))
    return BW

  def to_json(self):
    return {'bandwidth': self._bw}

  @staticmethod
  def from_json(obj):
    return Bandwidth(obj['bandwidth'])

  def __repr__(self):
    return str(self._bw)


class InfBandwidth(Bandwidth):

  def __init__(self):
    Bandwidth.__init__(self,float('inf'))

class BandwidthCollection:

  def __init__(self,bw):
    if not (isinstance(bw, Bandwidth)):
      raise Exception("not bandwidth: <%s>.T<%s>" % \
                      (bw,bw.__class__.__name__))
    self._bw = bw
    self._bindings = {}

  def update(self,new_bw):
    assert(isinstance(new_bw, Bandwidth))
    self._bw = new_bw

  def bind(self,name,bw):
    assert(isinstance(bw, Bandwidth))
    assert(not name in self._bindings)
    self._bindings[name] = bw

  def bindings(self):
    return self._bindings.items()

  @property
  def bandwidth(self):
    return self._bw

  def copy(self):
    ic = BandwidthCollection(self.bandwidth)
    for k,v in self.bindings():
      ic.bind(k,v)
    return ic

  def merge(self,other,new_bw):
    new_bws = self.copy()
    for k,v in other.bindings():
      new_bws.bind(k,v)

    new_bws.update(new_bw)
    return new_bws

  def __repr__(self):
    st = "bw %s\n" % self._bw
    for bnd,bw in self._bindings.items():
      st += "  %s: %s\n" % (bnd,bw)

    return st

