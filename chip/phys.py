import ops.nop as nops

class PhysicalModel:

  def __init__(self):
     self._delay = 0.0
     self._model = {}
     self._model[None] = nops.NZero()

  def set_model(self,model,cstr=None):
    assert(isinstance(model,nops.NOp))
    self._model[cstr] = model
    return self

  def default_model(self):
    return self._model[None]

  def set_delay(self,delay):
    self._delay = delay
    return self
