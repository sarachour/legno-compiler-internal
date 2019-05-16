import lab_bench.lib.enums as enums
import lab_bench.lib.chipcmd.data as chipdata
import lab_bench.lib.chipcmd.state as chipstate
from lab_bench.lib.chipcmd.data import *
from enum import Enum
import sqlite3
import util.config as CFG
import json
import binascii

class BlockStateDatabase:

  class Status(Enum):
    SUCCESS = "success"
    FAILURE = "failure"

  def __init__(self):
    path = CFG.STATE_DB
    self._conn = sqlite3.connect(path)
    self._curs = self._conn.cursor()

    cmd = '''
    CREATE TABLE IF NOT EXISTS states (
    cmdkey text NOT NULL,
    block text NOT NULL,
    status text NOT NULL,
    max_error real NOT NULL,
    state text NOT NULL,
    profile text NOT NULL,
    PRIMARY KEY (cmdkey)
    )
    '''
    self._curs.execute(cmd)
    self._conn.commit()
    self.keys = ['cmdkey','block','status','max_error','state','profile']

  def get_all(self):
    cmd = "SELECT * from states;"
    for values in self._curs.execute(cmd):
      yield dict(zip(self.keys,values))

  def put(self,blockstate,success=True,max_error=-1,profile=[]):
    assert(isinstance(blockstate,BlockState))
    key = blockstate.key.to_key()
    cmd = '''DELETE FROM states WHERE cmdkey="{cmdkey}"''' \
      .format(cmdkey=key)
    self._curs.execute(cmd)
    self._conn.commit()

    state_bits = blockstate.to_cstruct().hex()
    profile_bits = bytes(json.dumps(profile), 'utf-8').hex();

    status = BlockStateDatabase.Status.SUCCESS \
             if success else BlockStateDatabase.Status.FAILURE
    cmd = '''
    INSERT INTO states (cmdkey,block,status,max_error,state,profile)
    VALUES ("{cmdkey}","{block}","{status}",{max_error},"{state}","{profile}")
    '''.format(
      cmdkey=key,
      block=blockstate.block.value,
      status=status.value,
      max_error=max_error,
      state=state_bits,
      profile=profile_bits
    )
    self._curs.execute(cmd)
    self._conn.commit()

  def _get(self,blktype,loc,blockkey):
    assert(isinstance(blockkey,BlockState.Key))
    keystr = blockkey.to_key()
    cmd = '''SELECT * FROM states WHERE cmdkey = "{cmdkey}"''' \
                                                .format(cmdkey=keystr)
    results = list(self._curs.execute(cmd))
    return results

  def has(self,blktype,loc,blockkey):
    return len(self._get(blktype,loc,blockkey)) > 0

  def get(self,blktype,loc,blockkey):
    results = self._get(blktype,loc,blockkey)
    assert(len(results) == 1)
    data = dict(zip(self.keys,results[0]))
    state = data['state']
    obj = chipstate.BlockState \
                   .toplevel_from_cstruct(blktype,loc,
                                          bytes.fromhex(state))
    obj.profile = json.loads(bytes.fromhex(data['profile']).decode('utf-8'))
    obj.success = (data['status'] == BlockStateDatabase.Status.SUCCESS.value)
    obj.tolerance = data['max_error']
    return obj

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
          elif isinstance(value,float):
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
    self.success = None
    self.tolerance = None
    self.profile = []
    if state != None:
      self.from_cstruct(state)

  @staticmethod
  def toplevel_from_cstruct(blk,loc,data):
    pad = bytes([0]*(24-len(data)))
    typ = cstructs.state_t()
    obj = typ.parse(data+pad)
    if blk == enums.BlockType.FANOUT:
      st = FanoutBlockState(loc,obj.fanout)
    elif blk == enums.BlockType.INTEG:
      st = IntegBlockState(loc,obj.integ)
    elif blk == enums.BlockType.MULT:
      st = MultBlockState(loc,obj.mult)
    elif blk == enums.BlockType.DAC:
      st = DacBlockState(loc,obj.dac)
    elif blk == enums.BlockType.ADC:
      st = AdcBlockState(loc,obj.adc)
    elif blk == enums.BlockType.LUT:
      st = LutBlockState(loc,obj.lut)

    else:
      raise Exception("unimplemented block : <%s>" \
                      % blk.name)
    return st

  @property
  def key(self):
    raise NotImplementedError

  def from_cstruct(self,state):
    raise NotImplementedError

  def to_cstruct(self):
    raise NotImplementedError


  def __repr__(self):
    s = ""
    for k,v in self.__dict__.items():
      s += "%s=%s\n" % (k,v)
    return s

class LutBlockState(BlockState):

  class Key(BlockState.Key):

    def __init__(self,loc,source):
      BlockState.Key.__init__(self,enums.BlockType.LUT,loc)
      self.source = source


  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.DAC,loc,state)

  @property
  def key(self):
    return LutBlockState.Key(self.loc,
                             self.source)


  def to_cstruct(self):
    return cstructs.state_t().build({
      "lut": {
        "source": self.source.code(),
      }
    })


  def from_cstruct(self,state):
    self.source = chipdata.LUTSourceType(state.source)

class DacBlockState(BlockState):

  class Key(BlockState.Key):

    def __init__(self,loc,inv,rng,source,const_val):
      BlockState.Key.__init__(self,enums.BlockType.DAC,loc)
      self.inv = inv
      self.rng = rng
      self.source = source
      self.const_val = const_val


  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.DAC,loc,state)

  @property
  def key(self):
    return DacBlockState.Key(self.loc,
                             self.inv,
                             self.rng,
                             self.source,
                             self.const_val)


  def to_cstruct(self):
    return cstructs.state_t().build({
      "dac": {
        "enable": True,
        "inv": self.inv.code(),
        "range": self.rng.code(),
        "source": self.source.code(),
        "pmos": self.pmos,
        "nmos": self.nmos,
        "gain_cal": self.gain_cal,
        "const_code": self.const_code,
        "const_val": self.const_val
      }
    })

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

def to_c_list(keymap,value_code=True):
  intmap = {}
  for k,v in keymap.items():
    print("%s=%s" % (k,v))
    intmap[k.code()] = v.code() if value_code else v

  n = max(intmap.keys())
  buf = [0]*(n+1)
  for k,v in intmap.items():
    buf[k] = v
  return buf


class MultBlockState(BlockState):

  class Key(BlockState.Key):

    def __init__(self,loc,
                 vga,
                 invs,
                 ranges,
                 gain_val=None):
      BlockState.Key.__init__(self,enums.BlockType.MULT,loc)
      assert(isinstance(vga,chipdata.BoolType))
      self.invs = invs
      self.ranges = ranges
      self.gain_val = float(gain_val)
      self.vga = vga

  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.MULT,loc,state)

  def to_cstruct(self):
    return cstructs.state_t().build({
      "mult": {
        "vga": self.vga.code(),
        "enable": chipdata.BoolType.TRUE.code(),
        "inv": to_c_list(self.invs),
        "range": to_c_list(self.ranges),
        "pmos": self.pmos,
        "nmos": self.nmos,
        "port_cal": to_c_list(self.port_cals,value_code=False),
        "gain_cal": self.gain_cal,
        "gain_code": self.gain_code,
        "gain_val": self.gain_val
      }
    })

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
    self.vga = chipdata.BoolType(state.vga)
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
                 cal_enables,
                 invs,
                 ranges,
                 ic_val=None):
      BlockState.Key.__init__(self,enums.BlockType.INTEG,loc)
      self.exception = exception
      self.invs = invs
      self.cal_enables = cal_enables
      self.ranges = ranges
      self.ic_val = ic_val

  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.INTEG,loc,state)

  @property
  def key(self):
    return IntegBlockState.Key(self.loc,
                              self.exception,
                               self.cal_enable,
                               self.invs,
                               self.ranges, \
                               self.ic_val)

  def to_cstruct(self):
    return cstructs.state_t().build({
      "integ": {
        "cal_enable": to_c_list(self.cal_enable),
        "inv": to_c_list(self.invs),
        "enable": chipdata.BoolType.TRUE.code(),
        "exception": self.exception.code(),
        "range": to_c_list(self.ranges),
        "pmos": self.pmos,
        "nmos": self.nmos,
        "port_cal": to_c_list(self.port_cals,value_code=False),
        "ic_cal": self.ic_cal,
        "ic_code": self.ic_code,
        "ic_val": self.ic_val
      }
    })

  def from_cstruct(self,state):
    inid = enums.PortName.IN0
    outid = enums.PortName.OUT0
    self.enable = chipdata.BoolType(state.enable)
    self.exception = chipdata.BoolType(state.exception)

    self.cal_enable = {}
    self.cal_enable[inid] = chipdata \
        .BoolType(state.cal_enable[inid.code()])
    self.cal_enable[outid] = chipdata \
        .BoolType(state.cal_enable[inid.code()])

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
                 rngs):
      BlockState.Key.__init__(self,enums.BlockType.FANOUT,loc)
      self.invs = invs
      self.rngs = rngs
      self.third = third

  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.FANOUT,loc,state)


  @property
  def key(self):
    return FanoutBlockState.Key(self.loc,
                                self.third,
                                self.invs, \
                                self.rngs)

  def to_cstruct(self):
    return cstructs.state_t().build({
      "fanout": {
        "inv": to_c_list(self.invs),
        "enable": chipdata.BoolType.TRUE.code(),
        "third": self.third.code(),
        "range": to_c_list(self.rngs),
        "pmos": self.pmos,
        "nmos": self.nmos,
        "port_cal": to_c_list(self.port_cals,value_code=False),
      }
    })

  def from_cstruct(self,state):
    inid = enums.PortName.IN0
    out0id = enums.PortName.OUT0
    out1id = enums.PortName.OUT1
    out2id = enums.PortName.OUT2

    self.enable = chipdata.BoolType(state.enable)
    self.third = chipdata.BoolType(state.third)

    self.rngs = {}
    for ident in [inid,out0id,out1id,out2id]:
      self.rngs[ident] = chipdata.RangeType(state.range[inid.code()])

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
  def to_cstruct(self):
    return cstructs.state_t().build({
      "adc": {
        "test_en": self.test_en.code(),
        "test_adc": self.test_adc.code(),
        "test_i2v": self.test_i2v.code(),
        "test_rs": self.test_rs.code(),
        "test_rsinc": self.test_rsinc.code(),
        "enable": chipdata.BoolType.TRUE.code(),
        "inv": self.inv.code(),
        "pmos": self.pmos,
        "nmos": self.nmos,
        "pmos2": self.pmos2,
        'i2v_cal': self.i2v_cal,
        'upper_fs': self.upper_fs,
        'upper': self.upper,
        'lower_fs': self.lower_fs,
        "lower": self.lower,
        "range": self.rng.code(),
      }
    })

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
