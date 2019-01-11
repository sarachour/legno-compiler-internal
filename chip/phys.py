import ops.nop as nops

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
    for breakpt in self._breakpoints:
      self._stumps[breakpt] = PhysicalModelStump()

  def add_break(self,brk):
    assert(not self._freeze)
    self._breakpoints.append(brk)
    self._breakpoints.sort()

  def stump(self,breakpt):
    assert(self._freeze)
    assert(breakpt in self._breakpoints)
    return self._stumps[breakpt]


  def to_json(self):
    assert(self._freeze)
    stumpdict = {}
    for breakpt,stump in self._stumps.items():
      stumpdict[breakpt] = stump.to_json()

    return {
      'breakpoints': list(self._breakpoints),
      'stumps': stumpdict
    }
  def get_stump(self,freq):
    if freq < self._breakpoints[0]:
      self.stump(self._breakpoints[0])

    for breakpt in self._breakpoints:
      if freq >= breakpt:
        return self.stump(breakpt)

    return self.stump(self._breakpoints[-1])
