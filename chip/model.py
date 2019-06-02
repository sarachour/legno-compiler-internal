

class PortModel():

  def __init__(self,block,loc,port,comp_mode,scale_mode):
    self._port = port
    self._block = block
    self._comp_mode = comp_mode
    self._scale_mode = scale_mode
    self._noise = 0.0
    self._bias = 0.0
    self._unc_bias = 0.0

  @property
  def comp_mode(self):
    return self._comp_mode

  @property
  def scale_mode(self):
    return self._scale_mode

  @property
  def block(self):
    return self._block

  @property
  def loc(self):
    return self._loc

  @property
  def port(self):
    return self._port

  @property
  def bias(self):
    return self._bias

  @bias.setter
  def bias(self,v):
    self._bias = v

  @property
  def bias_uncertainty(self):
    return self._unc_bias

  @bias_uncertainty.setter
  def bias_uncertainty(self,v):
    assert(v >= 0.0)
    self._unc_bias = v

  @property
  def noise(self):
    return self._noise


  @noise.setter
  def noise(self,v):
    assert(v >= 0.0)
    self._noise = v


class OutputModel(PortModel):


  def __init__(self,
               block,
               loc,
               port,
               comp_mode,
               scale_mode):
    PortModel.__init__(self,block,loc,port, \
                       comp_mode,scale_mode)
    self._gain = 1.0


class ModelDB:

  def __init__(self):
    pass

  def get(self,block,loc,port,comp_mode,scale_mode):
    raise Exception("error: cannot get")

  def put(self,model):
    print("error: cannot put")


