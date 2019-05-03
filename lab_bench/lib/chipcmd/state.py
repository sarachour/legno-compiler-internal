import lab_bench.lib.enums as enums
import lab_bench.lib.chipcmd.data as chipdata
from enum import Enum
import sqlite3
import util.config as CFG
import json
import binascii

class BlockStateDatabase:

  def __init__(self):
    path = CFG.STATE_DB
    self._conn = sqlite3.connect(path)
    self._curs = self._conn.cursor()

    cmd = '''
    CREATE TABLE IF NOT EXISTS states (
    cmdkey text NOT NULL,
    block text NOT NULL,
    state text NOT NULL,
    PRIMARY KEY (cmdkey)
    )
    '''
    self._curs.execute(cmd)
    self._conn.commit()

  def get(self,blockkey):
    assert(isinstance(blockkey,BlockState.Key))
    key = blockkey.to_key()
    raise NotImplementedError

  def put(self,blockstate):
    assert(isinstance(blockstate,BlockState))
    key = blockstate.key.to_key()
    value = blockstate.to_json()
    cmd = '''DELETE FROM states WHERE cmdkey="{cmdkey}"''' \
      .format(cmdkey=key)
    self._curs.execute(cmd)
    self._conn.commit()

    cmd = '''
    INSERT INTO states (cmdkey,block,state)
    VALUES ("{cmdkey}","{block}","{state}")
    '''.format(
      cmdkey=key,
      block=blockstate.block.value,
      state=binascii.hexlify(
        bytes(json.dumps(value),'utf-8')
      )
    )
    self._curs.execute(cmd)
    self._conn.commit()

  def get(self,blockkey):
    assert(isinstance(blockstate,BlockState.Key))
    key = blockstate.to_key()
    raise NotImplementedError


class BlockState:

  class Key:
    def __init__(self,blk,loc):
      self.block = blk
      self.loc = loc

    def to_json(self):
      return self.__dict__

    def to_key(self):
      obj = self.to_json()
      keys = list(obj.keys())
      sorted(keys)
      ident = ""
      for key in keys:
        value = obj[key]
        ident += "%s=" % key
        if isinstance(value,float):
          ident += "%.3f" % value
        elif isinstance(value,Enum):
          ident += "%s" % obj[key].name
        else:
          ident += str(value)
        ident += ";"
      return ident

  def __init__(self,block_type,loc,state):
    self.block = block_type
    self.loc = loc
    self.state = {}
    self.from_cstruct(state)

  def to_json(self):
    obj = self.__dict__
    obj['loc'] = obj['loc'].to_json()
    return obj

  @property
  def key(self):
    raise NotImplementedError

  def from_cstruct(self,state):
    raise NotImplementedError

  def to_cstruct(self):
    raise NotImplementedError


class DacBlockState(BlockState):

  class Key(BlockState.Key):

    def __init__(self,loc,inv,rng,const_val):
      BlockState.Key.__init__(self,enums.BlockType.DAC,loc)
      self.inv = inv
      self.rng = rng
      self.const_val = const_val


  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.DAC,loc,state)

  @property
  def key(self):
    return DacBlockState.Key(self.loc,
                             self.inv,
                             self.rng,
                             self.const_val)


  def from_cstruct(self,state):
    self.enable = chipdata.BoolType(state.enable)
    self.inv = chipdata.SignType(state.inv)
    self.rng = chipdata.RangeType(state.range)
    self.source = chipdata.DACSourceType(state.source)
    self.pmos = state.pmos
    self.nmos = state.nmos
    self.gain_cal = state.gain_cal
    self.const_code = state.const_code
    self.const_val = state.const_val
