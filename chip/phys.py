import ops.nop as nops
from ops.interval import Interval
import json

class PhysicalModelStump:

  def __init__(self):
    self._delay = nops.mkzero()
    self._noise = nops.mkzero()
    self._bias = nops.mkzero()

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

  def __repr__(self):
    s = "delay: %s\n" % self.delay
    s += "noise: %s\n" % self.noise
    s += "bias: %s\n" % self.bias
    return s

class PhysicalModel:

  def __init__(self,port):
    # stumps, indexed by starting breakpoint
    self._stumps = {}
    self._breakpoints = []
    self._freeze = False
    self._port = port

  @property
  def port(self):
    return self._port

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
      'stumps': stumpdict,
      'port': self._port
    }

  @staticmethod
  def from_json(obj):
    phys = PhysicalModel(obj['port'])
    for breakpt in obj['breakpoints']:
      phys.add_break(breakpt)

    phys.freeze()
    for index,stump_obj in obj['stumps'].items():
      stump = phys._stumps[int(index)]
      new_stump = PhysicalModelStump.from_json(stump_obj)
      stump.set_to(new_stump)

    return phys

  def _get_index(self,freq):
    if freq < self._breakpoints[0]:
      return 0

    for index,breakpt in enumerate(self._breakpoints):
      if freq >= breakpt:
        return index

    return len(self._breakpoints) - 1


  def get_stump(self,freq):
    return self._stumps[self._get_index(freq)]


  def set_to(self,other):
    assert(isinstance(other,PhysicalModel))
    self._breakpoints = other._breakpoints
    self._stumps = other._stumps
    self._freeze = other._freeze
    self._port = other._port

  def stumps(self):
    minf = 0
    brks = self._breakpoints
    for idx,_ in enumerate(self._breakpoints):
      yield Interval.type_infer(minf,brks[idx]), \
        self._stumps[idx]

      minf = brks[idx]

    if len(brks) > 0:
      yield Interval.type_infer(brks[len(brks)-1],None), \
        self._stumps[len(brks)-1]

  def get_stumps(self,freq):
    brks = self._breakpoints
    yield (0,min(brks[0],freq)),self._stumps[0]

    for idx,fmin in enumerate(brks[:-2]):
      fmax = brks[idx+1]
      if freq >= fmin:
        yield (fmin,min(fmax,freq)),self._stumps[idx]

    if freq > brks[-1]:
      idx = len(brks)-1
      yield (brks[idx],freq),self._stumps[idx]

  def noise(self,freq):
    if len(self._stumps) == 0:
      yield (0,freq),nops.mkzero()
      return

    for (fmin,fmax),stump in self.get_stumps(freq):
      yield (fmin,fmax),stump.noise

  def bias(self,freq):
    if len(self._stumps) == 0:
      yield (0,freq),nops.mkzero()
      return

    for (fmin,fmax),stump in self.get_stumps(freq):
      yield (fmin,fmax),stump.bias

  def delay(self,freq):
    # delay in degrees. To compute delay in seconds,
    # delay_deg/freq
    if len(self._stumps) == 0:
      return nops.mkzero()

    return self.get_stump(freq).delay

  @staticmethod
  def read(filename):
    with open(filename,'r') as fh:
      data = fh.read()
      obj = json.loads(data)
      return PhysicalModel.from_json(obj)

  def __repr__(self):
    last_brk = "-inf"
    s = ""
    for idx,brk in enumerate(self._breakpoints):
      s += "{{ [%s,%s] Hz}}\n" % (last_brk,brk)
      stump = self._stumps[idx]
      s += str(stump)
      s += "\n\n"
      last_brk = brk

    if len(self._breakpoints) > 0:
      brk = "inf"
      s += "{{ [%s,%s] Hz}}\n" % (last_brk,brk)
      s += str(stump)

    return s
