import ops.nop as nops
import json

class PhysicalModelStump:

  def __init__(self):
    self._delay = nops.NZero()
    self._noise = nops.NZero()
    self._bias = nops.NZero()

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
    stump = PhysicalModelStump()
    stump.delay = nops.NOp.from_json(obj['delay'])
    stump.noise = nops.NOp.from_json(obj['noise'])
    stump.bias = nops.NOp.from_json(obj['bias'])
    return stump

  def set_to(self,other):
    assert(isinstance(other,PhysicalModelStump))
    self.delay = other.delay
    self.noise = other.noise
    self.bias = other.bias

  def to_json(self):
    return {
      'delay': self.delay.to_json(),
      'noise': self.noise.to_json(),
      'bias': self.bias.to_json()
    }

class PhysicalModel:

  def __init__(self):
    # stumps, indexed by starting breakpoint
    self._stumps = {}
    self._breakpoints = []
    self._freeze = False

  def freeze(self):
    self._freeze = True
    for index,_ in enumerate(self._breakpoints):
      self._stumps[index] = PhysicalModelStump()

  def add_break(self,brk):
    assert(not self._freeze)
    self._breakpoints.append(brk)
    self._breakpoints.sort()

  def stump(self,breakpt):
    assert(self._freeze)
    assert(breakpt in self._breakpoints)
    index = self._breakpoints.index(breakpt)
    return self._stumps[index]


  def to_json(self):
    assert(self._freeze)
    stumpdict = {}
    for index,stump in self._stumps.items():
      stumpdict[index] = stump.to_json()

    return {
      'breakpoints': list(self._breakpoints),
      'stumps': stumpdict
    }

  @staticmethod
  def from_json(obj):
    phys = PhysicalModel()
    for breakpt in obj['breakpoints']:
      phys.add_break(breakpt)

    phys.freeze()
    for index,stump_obj in obj['stumps'].items():
      stump = phys._stumps[int(index)]
      new_stump = PhysicalModelStump.from_json(stump_obj)
      stump.set_to(new_stump)

    return phys

  def get_stump(self,freq):
    if freq < self._breakpoints[0]:
      self.stump(self._breakpoints[0])

    for index,breakpt in enumerate(self._breakpoints):
      if freq >= breakpt:
        return self.stump(breakpt)

    return self.stump(self._breakpoints[-1])

  def set_to(self,other):
    assert(isinstance(other,PhysicalModel))
    self._breakpoints = other._breakpoints
    self._stumps = other._stumps
    self._freeze = other._freeze

  @staticmethod
  def read(filename):
    with open(filename,'r') as fh:
      data = fh.read()
      obj = json.loads(data)
      return PhysicalModel.from_json(obj)
