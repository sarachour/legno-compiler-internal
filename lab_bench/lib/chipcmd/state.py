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
      def dict_to_key(obj):
        keys = list(obj.keys())
        sorted(keys)
        ident = ""
        for key in keys:
          value = obj[key]
          ident += "%s=" % key
          if isinstance(value,dict):
            ident += "{%s}" % dict_to_key(value)
          if isinstance(value,float):
            ident += "%.3f" % value
          elif isinstance(value,Enum):
            ident += "%s" % obj[key].name
          else:
            ident += str(value)
          ident += ";"
        return ident

      return dict_to_key(obj)

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

class MultBlockState(BlockState):

  class Key(BlockState.Key):

    def __init__(self,loc,
                 vga,
                 invs,
                 ranges,
                 gain_val=None):
      BlockState.Key.__init__(self,enums.BlockType.MULT,loc)
      self.invs = invs
      self.ranges = ranges
      self.gain_val = gain_val
      self.vga = vga

  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.MULT,loc,state)

  @property
  def key(self):
    return MultBlockState.Key(self.loc,
                              self.vga,
                              self.invs,
                              self.ranges,
                              self.gain_val)

  def from_cstruct(self,state):
    in0id = enums.PortName.IN0
    in1id = enums.PortName.IN1
    outid = enums.PortName.OUT0
    self.enable = chipdata.BoolType(state.enable)
    self.vga = state.vga
    self.invs = {}
    self.invs[in0id] = chipdata.SignType(state.inv[in0id.code()])
    self.invs[in1id] = chipdata.SignType(state.inv[in1id.code()])
    self.invs[outid] = chipdata.SignType(state.inv[outid.code()])

    self.ranges = {}
    self.ranges[in0id] = chipdata.RangeType(state.range[in0id.code()])
    self.ranges[in1id] = chipdata.RangeType(state.range[in1id.code()])
    self.ranges[outid] = chipdata.RangeType(state.range[outid.code()])

    self.gain_val = state.gain_val

    self.pmos = state.pmos
    self.nmos = state.nmos
    self.port_cals = {}
    self.port_cals[in0id] = state.port_cal[in0id.code()]
    self.port_cals[in1id] = state.port_cal[in1id.code()]
    self.port_cals[outid] = state.port_cal[outid.code()]
    self.gain_cal = state.gain_cal
    self.gain_code = state.gain_code



class IntegBlockState(BlockState):

  class Key(BlockState.Key):

    def __init__(self,loc,
                 exception,
                 invs,
                 ranges,
                 ic_val=None):
      BlockState.Key.__init__(self,enums.BlockType.INTEG,loc)
      self.exception = exception
      self.invs = invs
      self.ranges = ranges
      self.ic_val = ic_val

  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.INTEG,loc,state)

  @property
  def key(self):
    return IntegBlockState.Key(self.loc,
                              self.exception,
                              self.invs,
                              self.ranges,
                              self.ic_val)

  def from_cstruct(self,state):
    inid = enums.PortName.IN0
    outid = enums.PortName.OUT0

    self.enable = chipdata.BoolType(state.enable)
    self.exception = chipdata.BoolType(state.exception)

    self.invs = {}
    self.invs[inid] = chipdata.SignType(state.inv[inid.code()])
    self.invs[outid] = chipdata.SignType(state.inv[outid.code()])

    self.ranges = {}
    self.ranges[inid] = chipdata.RangeType(state.range[inid.code()])
    self.ranges[outid] = chipdata.RangeType(state.range[outid.code()])

    self.ic_val = state.ic_val

    self.pmos = state.pmos
    self.nmos = state.nmos
    self.port_cals = {}
    self.port_cals[inid] = state.port_cal[inid.code()]
    self.port_cals[outid] = state.port_cal[outid.code()]
    self.ic_cal = state.ic_cal
    self.ic_code = state.ic_code



class FanoutBlockState(BlockState):

  class Key(BlockState.Key):

    def __init__(self,loc,
                 third,
                 invs,
                 rng):
      BlockState.Key.__init__(self,enums.BlockType.FANOUT,loc)
      self.invs = invs
      self.rng = rng
      self.third = third

  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.FANOUT,loc,state)


  @property
  def key(self):
    return FanoutBlockState.Key(self.loc,
                                self.third,
                                self.invs, \
                                self.rng)

  def from_cstruct(self,state):
    inid = enums.PortName.IN0
    out0id = enums.PortName.OUT0
    out1id = enums.PortName.OUT1
    out2id = enums.PortName.OUT2

    self.enable = chipdata.BoolType(state.enable)
    self.third = chipdata.BoolType(state.third)

    self.rng = chipdata.RangeType(state.range[inid.code()])
    self.invs = {}
    for ident in [out0id,out1id,out2id]:
      self.invs[ident] = chipdata.SignType(state.inv[ident.code()])


    self.pmos = state.pmos
    self.nmos = state.nmos

    self.port_cals = {}
    for ident in [out0id,out1id,out2id]:
      self.port_cals[ident] = state.port_cal[ident.code()]



class AdcBlockState(BlockState):

  class Key(BlockState.Key):

    def __init__(self,loc,
                 test_en,
                 test_adc,
                 test_i2v,
                 test_rs,
                 test_rsinc,
                 inv,
                 rng):
      BlockState.Key.__init__(self,enums.BlockType.ADC,loc)
      self.test_en = test_en
      self.test_adc = test_adc
      self.test_i2v = test_i2v
      self.test_rs = test_rs
      self.test_rsinc = test_rsinc
      self.inv = inv
      self.rng = rng

  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.ADC,loc,state)

  @property
  def key(self):
    return AdcBlockState.Key(self.loc,
                             self.test_en,
                             self.test_adc,
                             self.test_i2v,
                             self.test_rs,
                             self.test_rsinc,
                             self.inv,
                             self.rng
    )

  def from_cstruct(self,state):
    inid = enums.PortName.IN0
    outid = enums.PortName.OUT0

    self.test_en = chipdata.BoolType(state.test_en)
    self.test_adc = chipdata.BoolType(state.test_adc)
    self.test_i2v = chipdata.BoolType(state.test_i2v)
    self.test_rs = chipdata.BoolType(state.test_rs)
    self.test_rsinc = chipdata.BoolType(state.test_rsinc)
    self.enable = chipdata.BoolType(state.enable)
    self.inv = chipdata.SignType(state.inv)


    self.pmos = state.pmos
    self.nmos = state.nmos
    self.pmos2 = state.pmos2
    self.i2v_cal = state.i2v_cal
    self.upper_fs = state.upper_fs
    self.lower_fs = state.lower_fs
    self.upper = state.upper
    self.lower = state.lower
    self.rng = chipdata.RangeType(state.range)
