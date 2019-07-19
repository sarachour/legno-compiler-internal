import util.config as CFG
import util.util as util
import sqlite3
import json
import binascii
import math

class PortModel():

  def __init__(self,block,loc,port,comp_mode,scale_mode,handle=None):
    self._port = port
    self._block = block
    self._loc = loc
    self._handle = handle
    self._gain = 1.0
    self._noise = 0.0
    self._bias = 0.0
    self._unc_bias = 0.0
    # the actual lower bound is [ospos*pos, osneg*neg]
    self._opscale = (1.0,1.0)
    self._comp_mode = util.normalize_mode(comp_mode)
    self._scale_mode = util.normalize_mode(scale_mode)

  @staticmethod
  def from_json(obj):
    m = PortModel(None,None,None,None,None,None)
    m.__dict__ = obj
    m._comp_mode = util.normalize_mode(m._comp_mode)
    m._scale_mode = util.normalize_mode(m._scale_mode)
    return m

  def set_model(self,other):
    self._gain = other._gain
    self._noise = other._noise
    self._bias = other._bias
    self._unc_bias = other._unc_bias
    l,u = self._opscale
    self._opscale = (l,u)

  @property
  def gain(self):
    return self._gain

  @gain.setter
  def gain(self,v):
    assert(v > 0.0)
    self._gain = v

  @property
  def oprange_scale(self):
    return self._opscale

  def set_oprange_scale(self,a,b):
    assert(a >= 0 and a <= 1.0)
    assert(b >= 0 and b <= 1.0)
    self._opscale = (a,b)

  @property
  def identifier(self):
    ident = "%s-%s-%s-%s-%s-%s" % (self.block,self.loc,self.port,
                                   self.comp_mode,
                                   self.scale_mode,
                                   self.handle)
    return ident

  def to_json(self):
    return self.__dict__

  @property
  def comp_mode(self):
    return self._comp_mode

  @property
  def scale_mode(self):
    return self._scale_mode

  @property
  def handle(self):
    return self._handle


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

  def __repr__(self):
    r = "=== model ===\n"
    r += "ident: %s\n" % (self.identifier)
    r += "bias: mean=%f std=%f\n" % (self.bias,self.bias_uncertainty)
    r += "gain: mean=%f\n" % (self.gain)
    r += "noise: std=%f\n" % (self.noise)
    l,u = self._opscale
    r += ("scale=(%fx,%fx)\n" % (l,u))
    return r


class ModelDB:

  MISSING = []
  def __init__(self):
    path = CFG.MODEL_DB
    self._conn = sqlite3.connect(path)
    self._curs = self._conn.cursor()

    cmd = '''
    CREATE TABLE IF NOT EXISTS models (
    id int NOT NULL,
    block text NOT NULL,
    loc text NOT NULL,
    port text NOT NULL,
    comp_mode text NOT NULL,
    scale_mode text NOT NULL,
    handle text NOT NULL,
    model text NOT NULL,
    PRIMARY KEY (id)
    )
    '''
    self._curs.execute(cmd)
    self._conn.commit()
    self.keys = ['id',
                 'block',
                 'loc',
                 'port',
                 'comp_mode',
                 'scale_mode',
                 'handle',
                 'model']


  @staticmethod
  def log_missing_model(block_name,loc,port,comp_mode,scale_mode):
    ModelDB.MISSING.append((block_name,loc,port,comp_mode,scale_mode))

  def get_all(self):
    cmd = '''
    SELECT * from models
    '''
    for values in self._curs.execute(cmd):
      data = dict(zip(self.keys,values))
      yield self._process(data)

  def _process(self,data):
    obj = json.loads(bytes.fromhex(data['model']) \
                             .decode('utf-8'))

    model = PortModel.from_json(obj)
    return model


  def get_by_block(self,block,loc,comp_mode,scale_mode):
    model = PortModel(block,loc,"",comp_mode,scale_mode,None)
    cmd = '''
    SELECT * from models WHERE
    block = "{block}"
    AND loc = "{loc}"
    AND comp_mode = "{comp_mode}"
    AND scale_mode = "{scale_mode}"
    '''.format(
      block=model.block,
      loc=model.loc,
      comp_mode=model.comp_mode,
      scale_mode=model.scale_mode,
    )
    for values in self._curs.execute(cmd):
      data = dict(zip(self.keys,values))
      yield self._process(data)


  def _get(self,block,loc,port,comp_mode,scale_mode,handle=None):
    model = PortModel(block,loc,port,comp_mode,scale_mode,handle)
    cmd = '''
    SELECT * from models WHERE
    block = "{block}"
    AND loc = "{loc}"
    AND port = "{port}"
    AND comp_mode = "{comp_mode}"
    AND scale_mode = "{scale_mode}"
    AND handle = "{handle}";
    '''.format(
      block=model.block,
      loc=model.loc,
      port=model.port,
      comp_mode=model.comp_mode,
      scale_mode=model.scale_mode,
      handle=model.handle
    )

    for values in self._curs.execute(cmd):
      data = dict(zip(self.keys,values))
      return self._process(data)

    return None

  def get(self,block,loc,port,comp_mode,scale_mode,handle):
    return self._get(block,loc,port, \
                     comp_mode,scale_mode,handle)

  def has(self,block,loc,port,comp_mode,scale_mode,handle):
    return not self._get(block,loc,port, \
                         comp_mode,scale_mode,handle) is None

  def remove(self,block,loc,port,comp_mode,scale_mode,handle=None):
    model = PortModel(block,loc,port,comp_mode,scale_mode,handle)
    cmd = '''
    DELETE FROM models WHERE id="{id}";
    '''.format(id=model.identifier)

    self._curs.execute(cmd)
    self._conn.commit()

  def put(self,model):
    model_bits = bytes(json.dumps(model.to_json()),'utf-8').hex()
    cmd =  '''
    INSERT INTO models (id,block,loc,port,comp_mode,scale_mode,handle,model)
    VALUES ("{id}","{block}","{loc}","{port}","{comp_mode}",
            "{scale_mode}","{handle}","{model}");
    '''.format(
      id=model.identifier,
      block=model.block,
      loc=str(model.loc),
      port=str(model.port),
      comp_mode=str(model.comp_mode),
      scale_mode=str(model.scale_mode),
      handle=str(model.handle),
      model=model_bits

    )
    self.remove(model.block,model.loc,model.port, \
                model.comp_mode,model.scale_mode,model.handle)
    assert(not self.has(model.block,model.loc,model.port, \
                        model.comp_mode,model.scale_mode,model.handle))
    self._curs.execute(cmd)
    self._conn.commit()



def get_model(db,circ,block_name,loc,port,handle=None):
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    if db.has(block.name,loc,port, \
              config.comp_mode, \
              config.scale_mode,handle):
      model = db.get(block.name,loc,port, \
                     config.comp_mode, \
                     config.scale_mode,handle)
      return model
    else:
      assert(not config.scale_mode is None and \
             not config.scale_mode == "None")
      ModelDB.log_missing_model(block_name,loc,port, \
                                config.comp_mode,
                                config.scale_mode)
      #print("no model: %s[%s].%s :%s cm=%s scm=%s" % \
      #      (block_name,loc,port,handle, \
      #       str(config.comp_mode), \
      #       str(config.scale_mode)))
      return None

def get_variance(db,circ,block_name,loc,port,handle=None,mode='physical'):
  if mode == 'physical':
    #unc_min = 1e-6
    unc_min = 0.01
    model = get_model(db,circ,block_name,loc,port,handle=handle)
    if model is None:
      return unc_min

    unc = math.sqrt(model.noise**2.0 + model.bias_uncertainty**2.0)
    physunc = unc+abs(model.bias)
    if physunc == 0.0:
      return unc_min

    #print("%s[%s].%s uncertainty: %f" % (block_name, \
    #                                     loc, \
    #                                     port, \
    #                                     physunc))
    #return unc_min
    return physunc

  elif mode == 'ideal':
    return 1e-12
  elif mode == 'naive':
    return 0.01
  else:
    raise Exception("unknown mode")

def get_oprange_scale(db,circ,block_name,loc,port,handle=None,mode='physical'):
  if mode == 'physical':
    model = get_model(db,circ,block_name,loc,port,handle=handle)
    if model is None:
      return (1.0,1.0)

    l,u = model.oprange_scale
    return (l,u)

  elif mode == 'naive' or mode == 'ideal':
    return (1.0,1.0)

  else:
    raise Exception("unknown mode")

def get_gain(db,circ,block_name,loc,port,handle=None,mode='physical'):
  if mode == 'physical':
    model = get_model(db,circ,block_name,loc,port,handle=handle)
    if model is None:
      return 1.0

    return model.gain

  elif mode == 'naive' or mode == 'ideal':
    return 1.0

  else:
    raise Exception("unknown mode")
