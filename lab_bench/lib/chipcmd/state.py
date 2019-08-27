import lab_bench.lib.enums as enums
from lab_bench.lib.chipcmd import data as chipdata
from lab_bench.lib.chipcmd import state as chipstate
from lab_bench.lib.chipcmd.common import *
from lab_bench.lib.chipcmd.data import *
from enum import Enum
import sqlite3
import util.config as CFG
import util.util as util
import json
import binascii
import math

def keys(dict_,prefix=""):
  k = list(dict_.keys())
  k.sort()
  return list(map(lambda i: prefix+i, k))


def ordered(dict_):
  k = keys(dict_)
  v = []
  for key in k:
    v.append(dict_[key])

  return v


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
    chip int NOT NULL,
    tile int NOT NULL,
    slice int NOT NULL,
    idx int NOT NULL,
    calib_mode text NOT NULL,
    state text NOT NULL,
    profile text NOT NULL,
    PRIMARY KEY (cmdkey)
    )
    '''
    self._curs.execute(cmd)
    self._conn.commit()
    self.keys = ['cmdkey','block',
                 'chip','tile','slice','idx',
                 'calib_mode',
                 'state','profile']

  def get_all(self):
    cmd = "SELECT * from states;"
    for values in self._curs.execute(cmd):
      data = dict(zip(self.keys,values))
      result = self._process(data)
      if result is None:
        print("==== FAILED TO PROCESS ===")
        print(data)
        raise Exception("could not process row")

      yield result

  def get_by_instance(self,blk,chip,tile,slice,index, \
                      calib_mode=CalibType.MIN_ERROR):
    cmd = '''
    SELECT * from states WHERE block = "{block}" AND
                               chip = {chip} AND
                               tile = {tile} AND
                               slice = {slice} AND
                               idx = {index} AND
                               calib_mode = "{calib_mode}";
    '''.format(
      block=blk.value,
      chip=chip,
      tile=tile,
      slice=slice,
      index=index,
      calib_mode=calib_mode.value)

    for values in self._curs.execute(cmd):
      data = dict(zip(self.keys,values))
      result = self._process(data)
      yield result

  def put(self,blockstate,profile=[]):
    assert(isinstance(blockstate,BlockState))
    key = blockstate.key.to_key()
    cmd = '''DELETE FROM states WHERE cmdkey="{cmdkey}"''' \
      .format(cmdkey=key)
    self._curs.execute(cmd)
    self._conn.commit()

    print("PUT %s" % key)
    state_bits = blockstate.to_cstruct().hex()
    profile_bits = bytes(json.dumps(profile), 'utf-8').hex();
    cmd = '''
    INSERT INTO states (cmdkey,block,chip,tile,slice,idx,
                        calib_mode,state,profile)
    VALUES ("{cmdkey}","{block}",{chip},{tile},{slice},{index},
            "{calib_mode}","{state}","{profile}")
    '''.format(
      cmdkey=key,
      block=blockstate.block.value,
      chip=blockstate.loc.chip,
      tile=blockstate.loc.tile,
      slice=blockstate.loc.slice,
      index=blockstate.loc.index,
      calib_mode=blockstate.calib_mode.value,
      state=state_bits,
      profile=profile_bits
    )
    self._curs.execute(cmd)
    self._conn.commit()

  def _get(self,blockkey):
    assert(isinstance(blockkey,BlockState.Key))
    keystr = blockkey.to_key()
    print("GET %s" % keystr)
    cmd = '''SELECT * FROM states WHERE cmdkey = "{cmdkey}"''' \
                                                .format(cmdkey=keystr)
    results = list(self._curs.execute(cmd))
    return results

  def has(self,blockkey):
    return len(self._get(blockkey)) > 0

  def has_profile(self,blockkey):
    if self.has(blockkey):
      data = self.get(blockkey)
      if len(data.profile) == 0:
        return False
      else:
        return True
    else:
      return False

  def _process(self,data):
    state = data['state']
    loc = chipdata.CircLoc(data['chip'],
                  data['tile'],
                  data['slice'],
                  data['idx'])

    blk = enums.BlockType(data['block'])
    calib_mode = chipdata.CalibType(data['calib_mode'])
    try:
      obj = BlockState \
            .toplevel_from_cstruct(blk,loc, \
                                   bytes.fromhex(state), \
                                   calib_mode)
    except ValueError:
      return None

    obj.profile = json.loads(bytes.fromhex(data['profile']) \
                             .decode('utf-8'))
    return obj


  def get(self,blockkey):
    results = self._get(blockkey)
    if not (len(results) == 1):
      for row in self.get_all():
        print(row.key.to_key())
      raise Exception("cannot get <%s> : %d results found" \
                      % (blockkey.to_key(),len(results)))
    data = dict(zip(self.keys,results[0]))
    result = self._process(data)
    return result

class BlockState:

  class Key:
    def __init__(self,blk,loc,calib_mode=CalibType.MIN_ERROR):
      assert(isinstance(calib_mode,CalibType))
      self.block = blk
      self.loc = loc
      self.calib_mode = calib_mode

    @property
    def targeted_keys(self):
      print(self.block)
      raise NotImplementedError

    def to_json(self):
      obj = dict(self.__dict__)
      obj['loc'] = self.loc.to_json()
      obj['block'] = self.block.value
      return obj

    def to_key(self):
      obj = self.to_json()
      def dict_to_key(obj):
        keys = list(obj.keys())
        sorted(keys)
        ident = ""
        for key in keys:
          value = obj[key]
          if key in self.targeted_keys:
            continue

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

  def __init__(self,block_type,loc,state,calib_mode=CalibType.MIN_ERROR):
    self.block = block_type
    self.loc = loc
    self.calib_mode =calib_mode
    self.profile = []
    self.state = state
    if state != None:
      self.from_cstruct(state)

  def get_dataset(self,db,calib_mode):
    for obj in db.get_by_instance(
        self.block,
        self.loc.chip,
        self.loc.tile,
        self.loc.slice,
        self.loc.index,
        calib_mode):
      if len(obj.profile) == 0:
        continue

      keys = ['mode','in0','in1','out','bias','noise']
      prof = dict(map(lambda k : (k,[]), keys))
      for datum in obj.profile:
        for k in keys:
          prof[k].append(datum[k])

      yield {
        'metadata':obj.key.to_json(),
        'dataset':prof
      }

  def write_dataset(self,db):
    filepath = "%s/%s" % (CFG.DATASET_DIR, \
                          self.calib_mode.value)
    filename = "%s/%s_%d_%d_%d_%d.json" % (filepath,
                                           self.block.value,
                                           self.loc.chip,
                                           self.loc.tile,
                                           self.loc.slice,
                                           self.loc.index)
    dataset= []
    for datum in self.get_dataset(db,self.calib_mode):
      dataset.append(datum)

    objstr = json.dumps(dataset)
    util.mkdir_if_dne(filepath)
    with open(filename,'w') as fh:
      fh.write(objstr)



  @staticmethod
  def decode_cstruct(blk,data):
    pad = bytes([0]*(24-len(data)))
    typ = cstructs.state_t()
    obj = typ.parse(data+pad)
    if blk == enums.BlockType.FANOUT:
      return obj.fanout
    elif blk == enums.BlockType.INTEG:
      return obj.integ
    elif blk == enums.BlockType.MULT:
      return obj.mult
    elif blk == enums.BlockType.DAC:
      return obj.dac
    elif blk == enums.BlockType.ADC:
      return obj.adc
    elif blk == enums.BlockType.LUT:
      return obj.lut
    return obj

  @staticmethod
  def toplevel_from_cstruct(blk,loc,data,calib_mode):
    obj = BlockState.decode_cstruct(blk,data)
    assert(isinstance(calib_mode,CalibType))
    if blk == enums.BlockType.FANOUT:
      st = FanoutBlockState(loc,obj,calib_mode)
    elif blk == enums.BlockType.INTEG:
      st = IntegBlockState(loc,obj,calib_mode)
    elif blk == enums.BlockType.MULT:
      st = MultBlockState(loc,obj,calib_mode)
    elif blk == enums.BlockType.DAC:
      st = DacBlockState(loc,obj,calib_mode)
    elif blk == enums.BlockType.ADC:
      st = AdcBlockState(loc,obj,calib_mode)
    elif blk == enums.BlockType.LUT:
      st = LutBlockState(loc,obj,calib_mode)

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


    @property
    def targeted_keys(self):
      return []

  def __init__(self,loc,state,calib_mode):
    BlockState.__init__(self,enums.BlockType.LUT,loc,state,calib_mode)

  @property
  def key(self):
    return LutBlockState.Key(self.loc,
                             self.source)


  def to_rows(self,obj):
    return map(lambda i: (), [])

  def header(self):
    return [],[],[],[]

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

    def __init__(self,loc,inv,rng,source,const_val,calib_mode):
      BlockState.Key.__init__(self,enums.BlockType.DAC,loc,calib_mode)
      self.inv = inv
      self.rng = rng
      self.source = source
      self.const_val = const_val


    @property
    def targeted_keys(self):
      return ["const_val"]

  def __init__(self,loc,state,calib_mode):
    BlockState.__init__(self,enums.BlockType.DAC,loc, \
                        state,calib_mode)

  @property
  def key(self):
    return DacBlockState.Key(self.loc,
                             self.inv,
                             self.rng,
                             self.source,
                             self.const_val,
                             self.calib_mode)



  def header(self):
    GH = ['inv','rng','source','port']
    ZH = ["value"]
    YH = ["bias","noise"]
    XH = ["output"]
    return GH,ZH,XH,YH

  def to_rows(self,obj):
    G = [obj.inv.value,obj.rng,obj.source]
    Z = [obj.const_val]
    for port,target,in0,in1,bias,noise in obj.profile:
      GS = G + [port]
      Y = [bias,math.sqrt(noise)]
      X = [target]
      yield GS,Z,X,Y

  def update_value(self,value):
    self.const_val = value
    self.const_code = signed_float_to_byte(value)


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
                 gain_val=None,
                 calib_mode=CalibType.MIN_ERROR):
      BlockState.Key.__init__(self,enums.BlockType.MULT, \
                              loc,calib_mode)
      assert(isinstance(vga,chipdata.BoolType))
      self.invs = invs
      self.ranges = ranges
      self.gain_val = float(gain_val) \
                      if not gain_val is None else None
      self.vga = vga

    @property
    def targeted_keys(self):
      return ['gain_val']

  def __init__(self,loc,state,calib_mode):
    assert(isinstance(targeted,CalibType))
    BlockState.__init__(self,enums.BlockType.MULT,loc,state,calib_mode)

  def header(self):
    GH = keys(self.invs,prefix='inv-') + \
         keys(self.ranges,prefix='range-') + \
         ["vga","port"]
    ZH = ["gain"]
    YH = ["bias","noise"]
    XH = ["output","in0","in1/gain"]
    return GH,ZH,XH,YH

  def to_rows(self,obj):
    G = ordered(obj.invs) \
        + ordered(obj.ranges) \
        + [obj.vga.boolean()]
    Z = [obj.gain_val]
    for port,target,in0,in1,bias,noise in obj.profile:
      GS = G + [port]
      Y = [bias,math.sqrt(noise)]
      X = [target,in0,in1]
      yield GS,Z,X,Y

  def update_gain(self,value):
    self.gain_val = value
    self.gain_code = signed_float_to_byte(value)



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
                              self.gain_val,
                              self.calib_mode)



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
    self.gain_code = state.gain_code
    self.pmos = state.pmos
    self.nmos = state.nmos
    self.port_cals = {}
    self.port_cals[in0id] = state.port_cal[in0id.code()]
    self.port_cals[in1id] = state.port_cal[in1id.code()]
    self.port_cals[outid] = state.port_cal[outid.code()]
    self.gain_cal = state.gain_cal



class IntegBlockState(BlockState):

  class Key(BlockState.Key):

    def __init__(self,loc,
                 exception,
                 cal_enables,
                 invs,
                 ranges,
                 ic_val=None,
                 calib_mode=CalibType.MIN_ERROR):
      BlockState.Key.__init__(self,enums.BlockType.INTEG,loc,calib_mode)
      self.exception = exception
      self.invs = invs
      self.cal_enables = cal_enables
      self.ranges = ranges
      self.ic_val = ic_val

    @property
    def targeted_keys(self):
      return ['ic_val']

  def __init__(self,loc,state,calib_mode):
    BlockState.__init__(self,enums.BlockType.INTEG,loc,state,calib_mode)

  def header(self):
    gh = keys(self.invs,prefix='inv-') + \
         keys(self.ranges,prefix='range-') + \
         ["port"]
    zh = ['ic_val']
    yh = ["bias","noise"]
    xh = ["output"]
    return gh,zh,xh,yh

  def to_rows(self,obj):
    g = ordered(obj.invs) \
        + ordered(obj.ranges)
    z = [obj.ic_val]
    for port,target,in0,in1,bias,noise in obj.profile:
      gs = g + [port]
      y = [bias,math.sqrt(noise)]
      x = [target]
      yield gs,z,x,y


  @property
  def key(self):
    return IntegBlockState.Key(self.loc,
                              self.exception,
                               self.cal_enable,
                               self.invs,
                               self.ranges, \
                               self.ic_val,
                               self.calib_mode)


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

  def update_init_cond(self,value):
    self.ic_val = value
    self.ic_code = signed_float_to_byte(value)

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
                 rngs,
                 calib_mode):
      BlockState.Key.__init__(self,enums.BlockType.FANOUT,loc,calib_mode)
      self.invs = invs
      self.rngs = rngs
      self.third = third

    @property
    def targeted_keys(self):
      return []

  def __init__(self,loc,state,calib_mode):
    BlockState.__init__(self,enums.BlockType.FANOUT,loc,state,calib_mode)


  @property
  def key(self):
    return FanoutBlockState.Key(self.loc,
                                self.third,
                                self.invs, \
                                self.rngs, \
                                self.calib_mode)


  def header(self):
    gh = keys(self.invs,prefix='inv-') + \
         keys(self.rngs,prefix='range-') + \
         ["third", "port"]
    zh = []
    yh = ["bias","noise"]
    xh = ["output"]
    return gh,zh,xh,yh

  def to_rows(self,obj):
    g = ordered(obj.invs) \
        + ordered(obj.rngs) \
        + [obj.third.boolean()]
    z = []
    for port,target,in0,in1,bias,noise in obj.profile:
      gs = g + [port]
      y = [bias,math.sqrt(noise)]
      x = [target]
      yield gs,z,x,y



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
                 rng):
      BlockState.Key.__init__(self,enums.BlockType.ADC,loc)
      self.test_en = test_en
      self.test_adc = test_adc
      self.test_i2v = test_i2v
      self.test_rs = test_rs
      self.test_rsinc = test_rsinc
      self.rng = rng

    @property
    def targeted_keys(self):
      return []


  def __init__(self,loc,state):
    BlockState.__init__(self,enums.BlockType.ADC,loc,state)

  def to_rows(self,obj):
    g = [
      obj.rng,
      obj.test_en,
      obj.test_adc,
      obj.test_i2v,
      obj.test_rs,
      obj.test_rsinc,
    ]

    z = []
    for port,target,in0,in1,bias,noise in obj.profile:
      gs = g + [port]
      y = [bias,math.sqrt(noise)]
      x = [target]
      yield gs,z,x,y

  def header(self):
    gh = ['rng',
          'test_en',
          'test_adc',
          'test_i2v',
          'test_rs',
          'test_rsinc',
          'port']
    yh = ["bias","noise"]
    xh = ["output"]
    return gh,[],xh,yh

  @property
  def key(self):
    return AdcBlockState.Key(self.loc,
                             self.test_en,
                             self.test_adc,
                             self.test_i2v,
                             self.test_rs,
                             self.test_rsinc,
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
        "pmos": self.pmos,
        "nmos": self.nmos,
        "pmos2": self.pmos2,
        'i2v_cal': self.i2v_cal,
        'upper_fs': self.upper_fs,
        'upper': self.upper,
        'lower_fs': self.lower_fs,
        "lower": self.lower,
        "range": self.rng.code()
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


    self.pmos = state.pmos
    self.nmos = state.nmos
    self.pmos2 = state.pmos2
    self.i2v_cal = state.i2v_cal
    self.upper_fs = state.upper_fs
    self.lower_fs = state.lower_fs
    self.upper = state.upper
    self.lower = state.lower
    self.rng = chipdata.RangeType(state.range)
