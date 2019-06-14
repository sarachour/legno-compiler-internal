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
    self._comp_mode = util.normalize_mode(comp_mode)
    self._scale_mode = util.normalize_mode(scale_mode)

  @staticmethod
  def from_json(obj):
    m = PortModel(None,None,None,None,None,None)
    m.__dict__ = obj
    return m

  @property
  def gain(self):
    return self._gain

  @gain.setter
  def gain(self,v):
    assert(v > 0.0)
    self._gain = v


  @property
  def identifier(self):
    ident = "%s-%s-%s-%s-%s-%s" % (self.block,self.loc,self.port,
                                   self.comp_mode,
                                   self.scale_mode,
                                   self.handle)
    return hash(ident)

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
    r = "=== model ==="
    for k,v in self.__dict__.items():
      r += ("%s=%s\n" % (k,v))
    return r


class ModelDB:

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

    if "_gain" in obj:
      model = OutputModel.from_json(obj)

    else:
      model = PortModel.from_json(obj)

    return model


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

  def get(self,block,loc,port,comp_mode,scale_mode,handle=None):
    return self._get(block,loc,port, \
                     comp_mode,scale_mode,handle)

  def has(self,block,loc,port,comp_mode,scale_mode,handle=None):
    return not self._get(block,loc,port, \
                         comp_mode,scale_mode,handle) is None

  def remove(self,block,loc,port,comp_mode,scale_mode,handle=None):
    model = PortModel(block,loc,port,comp_mode,scale_mode,handle)
    id = model.identifier
    cmd = '''
    DELETE FROM models WHERE id="{id}"
    '''.format(id=id)

    self._curs.execute(cmd)
    self._conn.commit()

  def put(self,model):
    model_bits = bytes(json.dumps(model.to_json()),'utf-8').hex()
    cmd =  '''
    INSERT INTO models (id,block,loc,port,comp_mode,scale_mode,handle,model)
    VALUES ({id},"{block}","{loc}","{port}","{comp_mode}",
            "{scale_mode}","{handle}","{model}")
    '''.format(
      id=model.identifier,
      block=model.block,
      loc=str(model.loc),
      port=str(model.port),
      comp_mode=str(model.comp_mode),
      scale_mode=str(model.scale_mode),
      handle=model.handle,
      model=model_bits

    )
    self.remove(model.block,model.loc,model.port, \
                model.comp_mode,model.scale_mode,model.handle)
    self._curs.execute(cmd)
    self._conn.commit()

