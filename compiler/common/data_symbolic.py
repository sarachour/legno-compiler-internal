import ops.nop as nop
import util.util as util

class SymbolicExprTable:

  def __init__(self):
    self._tbl = {}

  def put(self,block,loc,port,model):
    assert(isinstance(model,SymbolicModel))
    self._tbl[(block,loc,port)] = model

  def get(self,block,loc,port):
    return self._tbl[(block,loc,port)]

  def has(self,block,loc,port):
    return (block,loc,port) in self._tbl

  def variables(self):
    for (blk,loc,port),model in self._tbl.items():
      yield blk,loc,port,model

  def clear(self):
    self._tbl = {}

class SymbolicModel:
  IGNORE_CHECKS = True

  def __init__(self,signal,mean,variance):
    assert(isinstance(signal,nop.NOp))
    assert(isinstance(mean,nop.NOp))
    assert(isinstance(variance,nop.NOp))
    self._signal = signal
    self._mean = mean
    self._variance = variance

  def idealized(self):
    return SymbolicModel(self.signal,nop.mkzero(),nop.mkzero())

  @staticmethod
  def from_expr(prop,sigexpr,nzexpr):
    prop.calculate_covariance = False
    sigm = prop.propagate_nop(sigexpr)
    phym = prop.propagate_nop(nzexpr)
    newm = SymbolicModel(sigm.mean,phym.mean,phym.variance)
    return newm

  @property
  def mean(self):
    return self._mean

  @property
  def signal(self):
    return self._signal

  def set_signal(self,s):
    assert(isinstance(s,nop.NOp))
    self._signal = s

  @property
  def variance(self):
    return self._variance

  def join(self,pwm):
    yield self,pwm


  def is_posynomial(self):
    if SymbolicModel.IGNORE_CHECKS:
      return True

    if not self.mean.is_posynomial() and not m.is_zero():
      return False
    if not self.variance.is_posynomial() and not v.is_zero():
      return False
    return True


  @staticmethod
  def from_json(hexstr):
    obj = util.decompress_json(hexstr)
    signal = nop.NOp.from_json(obj['signal'])
    mean = nop.NOp.from_json(obj['mean'])
    variance = nop.NOp.from_json(obj['variance'])
    model = SymbolicModel(signal,mean,variance)
    return model

  def to_json(self):
    obj= {
      'signal': self._signal.to_json(),
      'mean': self._mean.to_json(),
      'variance': self._variance.to_json()
    }
    hexstr = util.compress_json(obj)
    return hexstr

  def __repr__(self):
    s = "sig: %s\n" % self._signal
    s += "mean: %s\n" % self._mean
    s += "vari: %s\n" % self._variance
    return s
