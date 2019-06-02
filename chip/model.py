import util.config as CFG
import sqlite3
import json
import binascii
import math

class PortModel():

  def __init__(self,block,loc,port,comp_mode,scale_mode,tag=""):
    self._port = port
    self._block = block
    self._loc = loc
    self._comp_mode = comp_mode
    self._scale_mode = scale_mode
    self._tag = tag
    self._noise = 0.0
    self._bias = 0.0
    self._unc_bias = 0.0

  @property
  def identifier(self):
    ident = "%s-%s-%s-%s-%s-t%s" % (self.block,self.loc,self.port,
                                self.comp_mode,self.scale_mode,self.tag)
    print(ident)
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
  def block(self):
    return self._block

  @property
  def loc(self):
    return self._loc

  @property
  def port(self):
    return self._port

  @property
  def tag(self):
    return self._tag

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
               scale_mode,
               tag=""):
    PortModel.__init__(self,block,loc,port, \
                       comp_mode,scale_mode,tag)
    self._gain = 1.0


class ModelDB:

  def __init__(self):
    path = CFG.MODEL_DB
    self._conn = sqlite3.connect(path)
    self._curs = self._conn.cursor()

    cmd = '''
    CREATE TABLE IF NOT EXISTS models (
    id text NOT NULL,
    block text NOT NULL,
    loc text NOT NULL,
    comp_mode text NOT NULL,
    scale_mode text NOT NULL,
    tag text NOT NULL,
    model text NOT NULL,
    PRIMARY KEY (id)
    )
    '''
    self._curs.execute(cmd)
    self._conn.commit()
    self._keys = ['id',
                  'block',
                  'loc',
                  'comp_mode',
                  'scale_mode',
                  'tag',
                  'model']
  def get(self,block,loc,port,comp_mode,scale_mode,tag=""):
    model = PortModel(block,loc,port,comp_mode,scale_mode,tag)
    id = model.identifier
    cmd = '''
    SELECT * from models WHERE id="{id}")
    '''.format(id=id)

    for values in self._curs.execute(cmd):
      data = dict(zip(self.keys,values))
      self._process(data)

    raise Exception("doesn't exist")


  def remove(self,block,loc,port,comp_mode,scale_mode,tag=""):
    model = PortModel(block,loc,port,comp_mode,scale_mode,tag)
    id = model.identifier
    cmd = '''
    DELETE FROM models WHERE id="{id}"
    '''.format(id=id)

    self._curs.execute(cmd)
    self._conn.commit()

  def put(self,model):
    model_bits = bytes(json.dumps(model.to_json()),'utf-8').hex()
    cmd =  '''
    INSERT INTO models (id,block,loc,comp_mode,scale_mode,tag,model)
    VALUES ("{id}","{block}","{loc}","{comp_mode}","{scale_mode}","{tag}","{model}")
    '''.format(
      id=model.identifier,
      block=model.block,
      loc=str(model.loc),
      comp_mode=str(model.comp_mode),
      scale_mode=str(model.scale_mode),
      tag=model.tag,
      model=model_bits

    )
    self.remove(model.block,model.loc,model.port, \
                model.comp_mode,model.scale_mode,model.tag)
    self._curs.execute(cmd)
    self._conn.commit()

