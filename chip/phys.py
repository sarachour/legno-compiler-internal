import ops.nop as nops
from ops.interval import Interval
import json

class PhysicalModel:

  def __init__(self,port):
    self._delay = nops.mkzero()
    self._noise = nops.mkzero()
    self._bias = nops.mkzero()
    self._port = port

  @property
  def noise(self):
    return self._noise

  @noise.setter
  def noise(self,noise):
    assert(isinstance(noise, nops.NOp))
    self._noise = noise

  @property
  def bias(self):
    return self._bias

  @property
  def port(self):
    return self._port

  @bias.setter
  def bias(self,bias):
    assert(isinstance(bias, nops.NOp))
    self._bias = bias

  @property
  def delay(self):
    return self._delay

  @delay.setter
  def delay(self,delay):
    assert(isinstance(delay, nops.NOp))
    self._delay = delay

  @staticmethod
  def from_json(obj):
    stump = PhysicalModel(obj['port'])
    stump.delay = nops.NOp.from_json(obj['delay'])
    stump.noise = nops.NOp.from_json(obj['noise'])
    stump.bias = nops.NOp.from_json(obj['bias'])
    return stump

  @staticmethod
  def read(filename):
    with open(filename,'r') as fh:
      data = fh.read()
      obj = json.loads(data)
      return PhysicalModel.from_json(obj)

  def set_to(self,other):
    assert(isinstance(other,PhysicalModel))
    self.delay = other.delay
    self.noise = other.noise
    self.bias = other.bias

  def to_json(self):
    return {
      'delay': self.delay.to_json(),
      'noise': self.noise.to_json(),
      'bias': self.bias.to_json(),
      'port': self.port
    }

  def __repr__(self):
    s = "delay: %s\n" % self.delay
    s += "noise: %s\n" % self.noise
    s += "bias: %s\n" % self.bias
    return s
