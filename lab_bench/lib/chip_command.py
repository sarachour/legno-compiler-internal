import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
from lib.base_command import Command,ArduinoCommand, OptionalValue
import lib.util as util
import numpy as np
from enum import Enum
import construct
import math

class Priority(str,Enum):
    FIRST = "first"
    EARLY = "early"
    NORMAL = "normal"
    LATE = "late"
    LAST = "last"

    def priority(self):
        if self == Priority.FIRST:
            return 0
        elif self == Priority.EARLY:
            return 1
        elif self == Priority.NORMAL:
            return 2
        elif self == Priority.LATE:
            return 3
        elif self == Priority.LAST:
            return 4

class LUTSourceType(str,Enum):
    EXTERN = 'extern'
    ADC0 = "adc0"
    ADC1 = "adc1"



    def code(self):
        if self == LUTSourceType.EXTERN:
            return 0
        elif self == LUTSourceType.ADC0:
            return 1
        elif self == LUTSourceType.ADC1:
            return 2
        else:
            raise Exception("unknown: %s" % self)


    def abbrev(self):
        if self == LUTSourceType.EXTERN:
            return "ext"
        elif self == LUTSourceType.ADC0:
            return "adc0"
        elif self == LUTSourceType.ADC1:
            return "adc1"
        else:
            raise Exception("not handled: %s" % self)


    @staticmethod
    def from_abbrev(msg):
        if msg == 'ext':
            return LUTSourceType.EXTERN
        elif msg == 'adc0':
            return LUTSourceType.ADC0
        elif msg == 'adc1':
            return LUTSourceType.ADC1
        else:
            raise Exception("not handled: %s" % self)


class DACSourceType(str,Enum):
    # default
    MEM = 'memory'
    EXTERN = 'external'
    LUT0 = "lut0"
    LUT1 = "lut1"



    def code(self):
        if self == DACSourceType.MEM:
            return 0
        elif self == DACSourceType.EXTERN:
            return 1
        elif self == DACSourceType.LUT0:
            return 2
        elif self == DACSourceType.LUT1:
            return 3
        else:
            raise Exception("unknown: %s" % self)

    @staticmethod
    def from_abbrev(msg):
        if msg == 'mem':
            return DACSourceType.MEM
        elif msg == 'ext':
            return DACSourceType.EXTERN
        elif msg == 'lut0':
            return DACSourceType.LUT0
        elif msg == 'lut1':
            return DACSourceType.LUT1
        else:
            raise Exception("not handled: %s" % self)

    def abbrev(self):
        if self == DACSourceType.MEM:
            return "mem"
        elif self == DACSourceType.EXTERN:
            return "ext"
        elif self == DACSourceType.LUT0:
            return "lut0"
        elif self == DACSourceType.LUT1:
            return "lut1"
        else:
            raise Exception("not handled: %s" % self)


class RangeType(str,Enum):
    MED = 'medium'
    HIGH = 'high'
    LOW = 'low'

    @staticmethod
    def option_names():
        for opt in RangeType.options():
            yield opt.name

    @staticmethod
    def options():
        yield RangeType.MED
        yield RangeType.LOW
        yield RangeType.HIGH

    @staticmethod
    def from_abbrev(msg):
        if msg == 'm':
            return RangeType.MED
        elif msg == 'l':
            return RangeType.LOW
        elif msg == 'h':
            return RangeType.HIGH
        else:
            raise Exception("unknown range <%s>" % msg)

    def coeff(self):
        if self == RangeType.MED:
            return 1.0
        elif self == RangeType.LOW:
            return 0.1
        elif self == RangeType.HIGH:
            return 10.0
        else:
            raise Exception("unknown")

    def abbrev(self):
        if self == RangeType.MED:
            return "m"
        elif self == RangeType.LOW:
            return "l"
        elif self == RangeType.HIGH:
            return "h"

    def code(self):
        if self == RangeType.MED:
            return 1
        elif self == RangeType.LOW:
            return 0
        elif self == RangeType.HIGH:
            return 2
        else:
            raise Exception("unknown")

    def __repr__(self):
        return self.name

class SignType(str,Enum):
    POS = 'pos'
    NEG = 'neg'

    @staticmethod
    def option_names():
        for opt in SignType.options():
            yield opt.name


    @staticmethod
    def options():
        yield SignType.POS
        yield SignType.NEG

    @staticmethod
    def from_abbrev(msg):
        if msg == "+":
            return SignType.POS
        elif msg == "-":
            return SignType.NEG
        else:
            raise Exception("unknown")


    def coeff(self):
        if SignType.POS == self:
            return 1.0
        elif SignType.NEG == self:
            return -1.0
        else:
            raise Exception("unknown")

    def abbrev(self):
        if self == SignType.POS:
            return '+'
        elif self == SignType.NEG:
            return '-'
        else:
            raise Exception("unknown")

    def code(self):
        if self == SignType.POS:
            return False
        elif self == SignType.NEG:
            return True

    def __repr__(self):
        return self.abbrev()



def build_circ_ctype(circ_data):
    return {
        'test':ArduinoCommand.DEBUG,
        'type':enums.CmdType.CIRC_CMD.name,
        'data': {
            'circ_cmd':circ_data
        }
    }

def signed_float_to_byte(fvalue):
    assert(fvalue <= 1.0 and fvalue <= 1.0)
    value = int((fvalue+1.0)/2.0*255)
    assert(value >= 0 and value <= 255)
    return value

def float_to_byte(fvalue):
    assert(fvalue >= 0.0 and fvalue <= 1.0)
    value = int(fvalue*255)
    assert(value >= 0 and value <= 255)
    return value

def parse_pattern_conn(args,name):
    line = " ".join(args)

    src_cmds = [
        '{sblk:w} {schip:d} {stile:d} {sslice:d} {sindex:d} port {sport:d}',
        '{sblk:w} {schip:d} {stile:d} {sslice:d} port {sport:d}',
        '{sblk:w} {schip:d} {stile:d} {sslice:d} {sindex:d}',
        '{sblk:w} {schip:d} {stile:d} {sslice:d}'
    ]

    dst_cmds = [
        '{dblk:w} {dchip:d} {dtile:d} {dslice:d} {dindex:d} port {dport:d}',
        '{dblk:w} {dchip:d} {dtile:d} {dslice:d} port {dport:d}',
        '{dblk:w} {dchip:d} {dtile:d} {dslice:d} {dindex:d}',
        '{dblk:w} {dchip:d} {dtile:d} {dslice:d}'
    ]
    result = None
    for dst in dst_cmds:
        for src in src_cmds:
            if result is None:
                cmd = "%s %s %s" % (name,src,dst)
                result = parselib.parse(cmd,line)

    if result is None:
        return OptionalValue.error("usage:<%s>\nline:<%s>" % (cmd,line))

    result = dict(result.named.items())
    if not 'sindex' in result:
        result['sindex'] = None
    if not 'dindex' in result:
        result['dindex'] = None
    if not 'sport' in result:
        result['sport'] = None
    if not 'dport' in result:
        result['dport'] = None

    return OptionalValue.value(result)

def parse_pattern_block(args,n_signs,n_consts,n_range_codes, \
                        name,index=False,debug=False,source=None,expr=False):
    line = " ".join(args)
    DEBUG = {'debug':True,'prod':False}

    cmd = "%s {chip:d} {tile:d} {slice:d}" % name
    if index:
        cmd += " {index:d}"

    if not source is None:
        cmd += " src "
        cmd += "{source}"

    if n_signs > 0:
        cmd += " sgn "
        cmd += ' '.join(map(lambda idx: "{sign%d:W}" % idx,
                            range(0,n_signs)))
    if n_consts > 0:
        cmd += ' val '
        cmd += ' '.join(map(lambda idx: "{value%d:g}" % idx,
                           range(0,n_consts)))

    if n_range_codes > 0:
        cmd += ' rng '
        cmd += ' '.join(map(lambda idx: "{range%d:w}" % idx,
                           range(0,n_range_codes)))


    if debug:
        cmd += " {debug:w}"

    if expr:
        cmd += " {vars} {expr}"

    cmd = cmd.strip()
    result = parselib.parse(cmd,line)
    if result is None:
        msg = "usage: <%s>\n" % (cmd)
        msg += "line: <%s>" % line
        return OptionalValue.error(msg)

    result = dict(result.named.items())
    for idx in range(0,n_signs):
        key = 'sign%d' % idx
        value = result[key]
        result[key] = SignType.from_abbrev(value)

    for idx in range(0,n_range_codes):
        key = 'range%d' % idx
        value = result[key]
        result[key] = RangeType.from_abbrev(value)

    if not source is None:
        key = "source"
        value = result[key]
        result[key] = source.from_abbrev(value)

    if debug:
        result['debug'] = DEBUG[result['debug']]


    if expr:
        args = result['vars'].split('[')[1] \
                             .split(']')[0].split()
        result['vars'] = args


    return OptionalValue.value(result)


class CircLoc:

    def __init__(self,chip,tile,slice,index=None):
        self.chip = chip;
        self.tile = tile;
        self.slice = slice;
        self.index = index;

    def __hash__(self):
        return hash(str(self))

    def __eq__(self,other):
        if isinstance(other,CircLoc):
            return self.chip == other.chip \
                and self.tile == other.tile \
                and self.slice == other.slice \
                and self.index == other.index
        else:
            return False


    def build_ctype(self):
        if self.index is None:
            return {
                'chip':self.chip,
                'tile':self.tile,
                'slice':self.slice
            }
        else:
            return {
                'loc':{
                    'chip':self.chip,
                    'tile':self.tile,
                    'slice':self.slice
                },
                'idx':self.index
            }

    def __repr__(self):
        if self.index is None:
            return "loc(ch=%d,tile=%d.slice=%d)" % \
                (self.chip,self.tile,self.slice)
        else:
            return "loc(ch=%d,tile=%d,slice=%d,idx=%d)" % \
                (self.chip,self.tile,self.slice,self.index)

class CircPortLoc:

    def __init__(self,chip,tile,slice,port,index=None):
        self.loc = CircLoc(chip,tile,slice,index)
        assert(isinstance(port,int) or port is None)
        self.port = port

    def build_ctype(self):
        if self.loc.index is None:
            loc = CircLoc(self.loc.chip,
                          self.loc.tile,
                          self.loc.slice,
                          0)
        else:
            loc = self.loc

        port = self.port if not self.port is None else 0
        return {
            'idxloc':loc.build_ctype(),
            'idx2':port
        }

    def __hash__(self):
        return hash(str(self))


    def __eq__(self,other):
        if isinstance(other,CircPortLoc):
            return self.loc == other.loc and self.port == other.port
        else:
            return False

    def __repr__(self):
        return "port(%s,%s)" % (self.loc,self.port)


class AnalogChipCommand(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self,cstructs.cmd_t())

    def specify_index(self,block,loc):
        return (block == enums.BlockType.FANOUT) \
            or (block == enums.BlockType.TILE_INPUT) \
            or (block == enums.BlockType.TILE_OUTPUT) \
            or (block == enums.BlockType.MULT)

    def specify_output_port(self,block):
        return (block == enums.BlockType.FANOUT)

    def specify_input_port(self,block):
        return (block == enums.BlockType.MULT)


    def test_loc(self,block,loc):
        NCHIPS = 2
        NTILES = 4
        NSLICES = 4
        NINDICES_COMP = 2
        NINDICES_TILE = 4
        if not loc.chip in range(0,NCHIPS):
            self.fail("unknown chip <%d>" % loc.chip)
        if not loc.tile in range(0,NTILES):
            self.fail("unknown tile <%d>" % loc.tile)
        if not loc.slice in range(0,NSLICES):
            self.fail("unknown slice <%d>" % loc.slice)

        if (block == enums.BlockType.FANOUT) \
            or (block == enums.BlockType.TILE_INPUT) \
            or (block == enums.BlockType.TILE_OUTPUT) \
            or (block == enums.BlockType.MULT):
            indices = {
                enums.BlockType.FANOUT: range(0,NINDICES_COMP),
                enums.BlockType.MULT: range(0,NINDICES_COMP),
                enums.BlockType.TILE_INPUT: range(0,NINDICES_TILE),
                enums.BlockType.TILE_OUTPUT: range(0,NINDICES_TILE)
            }
            if loc.index is None:
                self.fail("expected index <%s>" % block)

            elif not loc.index in indices[block]:
                self.fail("block <%s> index <%d> must be from indices <%s>" %\
                          (block,loc.index,indices[block]))

        elif not block is None:
           if not loc.index is None:
               self.fail("expected no index <%s> <%d>" %\
                         (block,loc.index))

        else:
            self.fail("not in block list <%s>" % block)

    def priority(self):
        return Priority.EARLY

    def analyze(self):
        return None

    def calibrate(self):
        return None

    def disable(self):
        return None

    def configure(self):
        return None

    def apply(self,state):
        if state.dummy:
            return
        resp = ArduinoCommand.execute(self,state)
        return resp

class DisableCmd(AnalogChipCommand):

    def __init__(self,block,chip,tile,slice,index=None):
        AnalogChipCommand.__init__(self)
        self._block = enums.BlockType(block);
        self._loc = CircLoc(chip,tile,slice,index)
        self.test_loc(self._block,self._loc)

    def disable():
        return self

    def __eq__(self,other):
        if isinstance(other,DisableCmd):
            return self._loc == other._loc and \
                self._block.name == other._block.name
        else:
            return False

    def __hash__(self):
        return hash(str(self))

    @staticmethod
    def name():
        return 'disable'

    @staticmethod
    def desc():
        return "disable a block on the hdacv2 board"


    def build_ctype(self):
        if self._block == enums.BlockType.DAC:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_DAC.name,
                'data':{
                    'circ_loc':self._loc.build_ctype()
                }
            })
        if self._block == enums.BlockType.LUT:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_LUT.name,
                'data':{
                    'circ_loc':self._loc.build_ctype()
                }
            })

        if self._block == enums.BlockType.ADC:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_ADC.name,
                'data':{
                    'circ_loc':self._loc.build_ctype()
                }
            })

        elif self._block == enums.BlockType.MULT:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_MULT.name,
                'data':{
                    'circ_loc_idx1':self._loc.build_ctype()
                }
            })
        elif self._block == enums.BlockType.FANOUT:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_FANOUT.name,
                'data':{
                    'circ_loc_idx1':self._loc.build_ctype()
                }
            })
        elif self._block == enums.BlockType.INTEG:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_INTEG.name,
                'data':{
                    'circ_loc':self._loc.build_ctype()
                }
            })
        elif self._block == enums.BlockType.LUT:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_LUT.name,
                'data':{
                    'circ_loc':self._loc.build_ctype()
                }
            })
        else:
            print("no disable command <%s>" % self._block)
            return None


    def parse(args):
        result1 = parse_pattern_block(args[1:],0,0,0,
                                      "disable %s" % args[0],
                                      index=True)
        result2 = parse_pattern_block(args[1:],0,0,0,
                                      "disable %s" % args[0],
                                      index=False)

        if not result1 is None:
            return DisableCmd(args[0],
                              result1['chip'],
                              result1['tile'],
                              result1['slice'],
                              result1['index'])
        if not result2 is None:
            return DisableCmd(args[0],
                              result2['chip'],
                              result2['tile'],
                              result2['slice'])

    def __repr__(self):
        return "disable %s.%s" % (self._loc,self._block)

class CalibrateCmd(AnalogChipCommand):

    def __init__(self,chip,tile,slice):
        AnalogChipCommand.__init__(self)
        self._loc = CircLoc(chip,tile,slice)
        self.test_loc(enums.BlockType.NONE,self._loc)

    def calibrate(self):
        return self

    @staticmethod
    def name():
        return 'calibrate'

    @staticmethod
    def desc():
        return "calibrate a slice on the hdacv2 board"

    def build_ctype(self):
        return build_circ_ctype({
            'type':enums.CircCmdType.CALIBRATE.name,
            'data':{
                'circ_loc':{
                    'chip': self._loc.chip,
                    'tile': self._loc.tile,
                    'slice': self._loc.slice
                }
            }
        })


    def __hash__(self):
        return hash(self._loc)

    def __eq__(self,other):
        if isinstance(other,CalibrateCmd):
            return self._loc == other._loc
        else:
            return False

    def apply(self,state):
        resp = AnalogChipCommand.apply(self,state)

    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,0,0,0,
                                      CalibrateCmd.name(),
                                      index=False)
        if result.success:
            return CalibrateCmd(result['chip'],result['tile'],
                                result['slice'])
        else:
            print(result.message)
            raise Exception("<parse_failure>: %s" % args)

    def __repr__(self):
        return "calib %s" % self._loc


class UseCommand(AnalogChipCommand):

    def __init__(self,block,loc):
        AnalogChipCommand.__init__(self)
        self.test_loc(block,loc)
        self._loc = loc
        self._block = block

    @property
    def loc(self):
        return self._loc

    def priority(self):
        return Priority.FIRST

    def configure(self):
        return self

    def calibrate(self):
        return CalibrateCmd(
            self._loc.chip,
            self._loc.tile,
            self._loc.slice)

    def disable(self):
         return DisableCmd(
             self._block,
             self._loc.chip,
             self._loc.tile,
             self._loc.slice,
             self._loc.index)

    def __repr__(self):
        raise Exception("override me")

class ConstVal:
    #POS_BUF = np.arange(0.75,-0.8,-(0.8+0.75)/256)
    #NEG_BUF = np.arange(-0.8,0.8,(0.8+0.8)/256)
    NEG_BUF = np.arange(0.9375,-1.0,-(1.9375)/256)
    POS_BUF = np.arange(-1.0,1.0,(2.0)/256)

    @staticmethod
    def POS_get_closest(value):
        pos_dist,pos_near_val = util.find_closest(ConstVal.POS_BUF, \
                                          value,util.RoundMode.NEAREST)
        code = int(np.where(ConstVal.POS_BUF == pos_near_val)[0])
        return pos_near_val,code

    @staticmethod
    def NEG_get_closest(value):
        neg_dist,neg_near_val = util.find_closest(ConstVal.NEG_BUF, \
                                          value,util.RoundMode.NEAREST)
        code = int(np.where(ConstVal.NEG_BUF == neg_near_val)[0])
        return neg_near_val,code


    @staticmethod
    def get_closest(value):
        pos_dist,pos_near_val = util.find_closest(ConstVal.POS_BUF, \
                                          value,util.RoundMode.NEAREST)
        neg_dist,neg_near_val = util.find_closest(ConstVal.NEG_BUF, \
                                          value,util.RoundMode.NEAREST)
        if pos_dist <= neg_dist:
            inv = False
            code = int(np.where(ConstVal.POS_BUF == pos_near_val)[0])
            near_val = pos_near_val
        else:
            inv = True
            code = int(np.where(ConstVal.NEG_BUF == neg_near_val)[0])
            near_val = neg_near_val
        return near_val,inv,code

class WriteLUTCmd(UseCommand):

    def __init__(self,chip,tile,slice,variables,expr):
        UseCommand.__init__(self,
                            enums.BlockType.LUT,
                            CircLoc(chip,tile,slice))

        if not self._loc.index is None:
            self.fail("lut has no index <%d>" % loc.index)

        self._expr = expr
        self._variables = variables
        if not (len(self._variables) == 1):
            raise Exception('unexpected number of variables: %s' % variables)

    @property
    def expr(self):
        return self._expr

    @staticmethod
    def desc():
        return "write data to lut block on the hdacv2 board"


    @staticmethod
    def parse(args):
        return WriteLUTCmd._parse(args,WriteLUTCmd)

    @staticmethod
    def _parse(args,cls):
        result = parse_pattern_block(args,0,0,0,
                                     cls.name(),
                                     source=None,
                                     expr=True)
        if result.success:
            data = result.value
            return cls(
                data['chip'],
                data['tile'],
                data['slice'],
                data['vars'],
                data['expr']
            )
        else:
            raise Exception(result.message)

    def build_dtype(self,buf):
        return construct.Array(len(buf),
                        construct.Float32l)


    def build_ctype(self,offset=None,n=None):
        # inverting flips the sign for some wacky reason, given the byte
        # representation is signed
        return build_circ_ctype({
            'type':enums.CircCmdType.WRITE_LUT.name,
            'data':{
                'write_lut':{
                    'loc':self._loc.build_ctype(),
                    'offset':offset,
                    'n':n
                }
            }
        })

    @staticmethod
    def name():
        return 'write_lut'

    def __repr__(self):
        vstr = ",".join(self._variables)
        st = "%s %s %s %s [%s] %s" % \
              (self.name(),
               self.loc.chip,self.loc.tile, \
               self.loc.slice,
               vstr,self._expr)
        return st



    def apply(self,state):
        if state.dummy:
            return

        values = [-256.0]*256
        for idx,v in enumerate(np.linspace(-1.0,1.0,256)):
            assigns = dict(zip(self._variables,[v]))
            value = util.eval_func(self.expr,assigns)
            values[idx] = float(value)


        resp = ArduinoCommand.execute(self,state,
                                        {
                                            'raw_data':list(values),
                                            'n_data_bytes':128,
                                            'elem_size':4
                                        })
        return resp


class UseLUTCmd(UseCommand):

    def __init__(self,chip,tile,slice,
                 source=LUTSourceType.EXTERN):
        UseCommand.__init__(self,
                            enums.BlockType.LUT,
                            CircLoc(chip,tile,slice))

        if not self._loc.index is None:
            self.fail("dac has no index <%d>" % loc.index)

        self._source = source

    @property
    def expr(self):
        return self._expr

    @staticmethod
    def desc():
        return "use a lut block on the hdacv2 board"


    @staticmethod
    def parse(args):
        return UseLUTCmd._parse(args,UseLUTCmd)

    @staticmethod
    def _parse(args,cls):
        result = parse_pattern_block(args,0,0,0,
                                     cls.name(),
                                     source=LUTSourceType,
                                     expr=False)
        if result.success:
            data = result.value
            return cls(
                data['chip'],
                data['tile'],
                data['slice'],
                source=data['source']
            )
        else:
            raise Exception(result.message)


    def build_ctype(self):
        # inverting flips the sign for some wacky reason, given the byte
        # representation is signed
        return build_circ_ctype({
            'type':enums.CircCmdType.USE_LUT.name,
            'data':{
                'lut':{
                    'loc':self._loc.build_ctype(),
                    'source':self._source.code()
                }
            }
        })

    @staticmethod
    def name():
        return 'use_lut'

    def __repr__(self):
        st = "%s %s %s %s src %s" % \
              (self.name(),
               self.loc.chip,self.loc.tile, \
               self.loc.slice,
               self._source.abbrev())
        return st


    def apply(self,state):
        if state.dummy:
            return
        resp = AnalogChipCommand.apply(self,state)
        return resp


class UseADCCmd(UseCommand):

    def __init__(self,chip,tile,slice,
                 in_range=RangeType.MED):
        UseCommand.__init__(self,
                            enums.BlockType.ADC,
                            CircLoc(chip,tile,slice))

        if not self._loc.index is None:
            self.fail("adc has no index <%d>" % loc.index)

        assert(isinstance(in_range,RangeType))
        if in_range == RangeType.LOW:
            raise Exception("incompatible: low input")

        self._in_range = in_range

    @staticmethod
    def desc():
        return "use a constant adc block on the hdacv2 board"


    @staticmethod
    def parse(args):
        return UseADCCmd._parse(args,UseADCCmd)

    @staticmethod
    def _parse(args,cls):
        result = parse_pattern_block(args,0,0,1,
                                     cls.name())
        if result.success:
            data = result.value
            return cls(
                data['chip'],
                data['tile'],
                data['slice'],
                in_range=data['range0']
            )
        else:
            raise Exception(result.message)

    def build_ctype(self):
        # inverting flips the sign for some wacky reason, given the byte
        # representation is signed
        return build_circ_ctype({
            'type':enums.CircCmdType.USE_ADC.name,
            'data':{
                'adc':{
                    'loc':self._loc.build_ctype(),
                    'in_range':self._in_range.code()
                }
            }
        })

    @staticmethod
    def name():
        return 'use_adc'

    def __repr__(self):
        st = "%s %s %s %s rng %s" % \
              (self.name(),
               self.loc.chip,self.loc.tile, \
               self.loc.slice,
               self._in_range.abbrev())
        return st


class UseDACCmd(UseCommand):

    def __init__(self,chip,tile,slice,value,
                 source=DACSourceType.MEM,
                 out_range=RangeType.MED,
                 inv=SignType.POS):
        UseCommand.__init__(self,
                            enums.BlockType.DAC,
                            CircLoc(chip,tile,slice))

        if value < -1.0 or value > 1.0:
            self.fail("value not in [-1,1]: %s" % value)
        if not self._loc.index is None:
            self.fail("dac has no index <%d>" % loc.index)

        assert(isinstance(inv,SignType))
        assert(isinstance(out_range,RangeType))
        if out_range == RangeType.LOW:
            raise Exception("incompatible: low output")

        self._out_range = out_range
        self._value = value
        self._inv = inv
        self._source = source

    @staticmethod
    def desc():
        return "use a constant dac block on the hdacv2 board"


    @staticmethod
    def parse(args):
        return UseDACCmd._parse(args,UseDACCmd)

    @staticmethod
    def _parse(args,cls):
        result = parse_pattern_block(args,1,1,1,
                                     cls.name(),
                                     source=DACSourceType)
        if result.success:
            data = result.value
            return cls(
                data['chip'],
                data['tile'],
                data['slice'],
                data['value0'],
                source=data['source'],
                inv=data['sign0'],
                out_range=data['range0']
            )
        else:
            raise Exception(result.message)

    def build_ctype(self):
        # inverting flips the sign for some wacky reason, given the byte
        # representation is signed
        return build_circ_ctype({
            'type':enums.CircCmdType.USE_DAC.name,
            'data':{
                'dac':{
                    'loc':self._loc.build_ctype(),
                    'value':self._value,
                    # for whatever screwy reason, with inversion disabled
                    # 255=-1.0 and 0=1.0
                    'source':self._source.code(),
                    'inv':self._inv.code(),
                    'out_range':self._out_range.code()
                }
            }
        })

    @staticmethod
    def name():
        return 'use_dac'

    def __repr__(self):
        st = "%s %s %s %s src %s sgn %s val %s rng %s" % \
              (self.name(),
               self.loc.chip,self.loc.tile, \
               self.loc.slice,
               self._source.abbrev(),
               self._inv.abbrev(),
               self._value,
               self._out_range.abbrev())
        return st

class ConfigDACCmd(UseDACCmd):

    def __init__(self,chip,tile,slice,value,
                 out_range=RangeType.MED,\
                 source=DACSourceType.MEM, \
                 inv=SignType.POS):
        UseDACCmd.__init__(self,chip,tile,slice,value,
                           out_range=out_range,\
                           source=source, \
                           inv=inv)


    def build_ctype(self):
        # inverting flips the sign for some wacky reason, given the byte
        # representation is signed
        return build_circ_ctype({
            'type':enums.CircCmdType.CONFIG_DAC.name,
            'data':{
                'dac':{
                    'loc':self._loc.build_ctype(),
                    'value':self._value,
                    # for whatever screwy reason, with inversion disabled
                    # 255=-1.0 and 0=1.0
                    'inv':self._inv.code(),
                    'source':self._source.code(),
                    'out_range':self._out_range.code()
                }
            }
        })

    @staticmethod
    def name():
        return 'config_dac'


    def priority(self):
        return Priority.NORMAL

    @staticmethod
    def parse(args):
        return UseDACCmd._parse(args,ConfigDACCmd)



class GetADCStatusCmd(AnalogChipCommand):
    def __init__(self,chip,tile,slice):
        AnalogChipCommand.__init__(self)
        self._loc = CircLoc(chip,tile,slice)

    @property
    def loc(self):
        return self._loc

    @staticmethod
    def name():
        return 'get_adc_status'

    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,0,0,0,
                                     GetADCStatusCmd.name(),
                                     debug=False)
        if result.success:
            data = result.value
            return GetADCStatusCmd(
                data['chip'],
                data['tile'],
                data['slice']
            )
        else:
            raise Exception(result.message)


    def analyze(self):
        return self

    def build_ctype(self):
        # inverting flips the sign for some wacky reason, given the byte
        # representation is signed
        return build_circ_ctype({
            'type':enums.CircCmdType.GET_ADC_STATUS.name,
            'data':{
                'circ_loc':self._loc.build_ctype()
            }
        })

    def apply(self,state):
        if state.dummy:
            return

        resp = AnalogChipCommand.apply(self,state)
        handle = "adc.%s" % self.loc
        code = resp.data(0)
        print("status_val: %s" % code)
        state.set_status(handle, code)



    def __repr__(self):
        st = "get_adc_status %s %s %s" % \
              (self.loc.chip,self.loc.tile, \
               self.loc.slice)
        return st


class GetIntegStatusCmd(AnalogChipCommand):
    def __init__(self,chip,tile,slice):
        AnalogChipCommand.__init__(self)
        self._loc = CircLoc(chip,tile,slice)

    @property
    def loc(self):
        return self._loc

    @staticmethod
    def name():
        return 'get_integ_status'

    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,0,0,0,
                                     GetIntegStatusCmd.name(),
                                     debug=False)
        if result.success:
            data = result.value
            return GetIntegStatusCmd(
                data['chip'],
                data['tile'],
                data['slice']
            )
        else:
            raise Exception(result.message)


    def analyze(self):
        return self

    def build_ctype(self):
        # inverting flips the sign for some wacky reason, given the byte
        # representation is signed
        return build_circ_ctype({
            'type':enums.CircCmdType.GET_INTEG_STATUS.name,
            'data':{
                'circ_loc':self._loc.build_ctype()
            }
        })

    def apply(self,state):
        if state.dummy:
            return

        resp = AnalogChipCommand.apply(self,state)
        handle = "integ.%s" % self.loc
        oflow = True if resp.data(0) == 1 else False
        print("status_val: %s" % oflow)
        state.set_status(handle, oflow)



    def __repr__(self):
        st = "get_integ_status %s %s %s" % \
              (self.loc.chip,self.loc.tile, \
               self.loc.slice)
        return st



class UseIntegCmd(UseCommand):


    def __init__(self,chip,tile,slice,init_cond,
                 inv=SignType.POS, \
                 in_range=RangeType.MED, \
                 out_range=RangeType.MED,
                 debug=False):
        UseCommand.__init__(self,
                            enums.BlockType.INTEG,
                            CircLoc(chip,tile,slice))
        assert(isinstance(inv,SignType))
        assert(isinstance(in_range,RangeType))
        assert(isinstance(out_range,RangeType))
        if init_cond < -1.0 or init_cond > 1.0:
            self.fail("init_cond not in [-1,1]: %s" % init_cond)

        self._init_cond = init_cond
        self._inv = inv
        if in_range == RangeType.HIGH and \
           out_range == RangeType.LOW:
            raise Exception("incompatible: high input and low output")
        elif in_range == RangeType.LOW and \
             out_range == RangeType.HIGH:
            raise Exception("incompatible: high input and low output")

        self._in_range = in_range
        self._out_range = out_range
        self._debug = debug


    @staticmethod
    def desc():
        return "use a integrator block on the hdacv2 board"


    @staticmethod
    def parse(args):
        return UseIntegCmd._parse(args,UseIntegCmd)

    @staticmethod
    def _parse(args,cls):
        result = parse_pattern_block(args,1,1,2,
                                     cls.name(),
                                     debug=True)
        if result.success:
            data = result.value
            return cls(
                data['chip'],
                data['tile'],
                data['slice'],
                data['value0'],
                inv=data['sign0'],
                in_range=data['range0'],
                out_range=data['range1'],
                debug=data['debug']
            )
        else:
            raise Exception(result.message)


    @staticmethod
    def name():
        return 'use_integ'

    def build_ctype(self):
        return build_circ_ctype({
            'type':enums.CircCmdType.USE_INTEG.name,
            'data':{
                'integ':{
                    'loc':self._loc.build_ctype(),
                    'value':self._init_cond,
                    'inv':self._inv.code(),
                    'in_range': self._in_range.code(),
                    'out_range': self._out_range.code(),
                    'debug': 1 if self._debug else 0
                }
            }
        })

    def __repr__(self):
        fmtstr = "%s %d %d %d sgn %s val %f rng %s %s %s"
        st = fmtstr % (self.name(),
                       self.loc.chip, \
                       self.loc.tile, \
                       self.loc.slice, \
                       self._inv.abbrev(),
                       self._init_cond,
                       self._in_range.abbrev(),
                       self._out_range.abbrev(),
                       "debug" if self._debug else "prod")
        return st



class ConfigIntegCmd(UseIntegCmd):

    def __init__(self,chip,tile,slice,init_cond,
                 inv=SignType.POS, \
                 in_range=RangeType.MED, \
                 out_range=RangeType.MED,
                 debug=False):
        UseIntegCmd.__init__(self,chip,tile,slice,init_cond,
                         inv=inv,
                         in_range=in_range,
                         out_range=out_range,
                         debug=debug)

    def priority(self):
        return Priority.LATE


    @staticmethod
    def name():
        return 'config_integ'

    def build_ctype(self):
        return build_circ_ctype({
            'type':enums.CircCmdType.CONFIG_INTEG.name,
            'data':{
                'integ':{
                    'loc':self._loc.build_ctype(),
                    'value':self._init_cond,
                    'inv':self._inv.code(),
                    'in_range': self._in_range.code(),
                    'out_range': self._out_range.code(),
                    'debug': 1 if self._debug else 0
                }
            }
        })

    @staticmethod
    def parse(args):
        return UseIntegCmd._parse(args,cls=ConfigIntegCmd)


class UseFanoutCmd(UseCommand):


    def __init__(self,chip,tile,slice,index,
                 in_range,
                 inv0=False,inv1=False,inv2=False):

        assert(isinstance(inv0,SignType))
        assert(isinstance(inv1,SignType))
        assert(isinstance(inv2,SignType))
        assert(isinstance(in_range,RangeType))

        UseCommand.__init__(self,
                            enums.BlockType.FANOUT,
                            CircLoc(chip,tile,slice,index))
        if in_range == RangeType.LOW:
            raise Exception("incompatible: low output")

        self._inv = [inv0,inv1,inv2]
        self._inv0 = inv0
        self._inv1 = inv1
        self._inv2 = inv2
        self._in_range = in_range

    @staticmethod
    def name():
        return 'use_fanout'

    @staticmethod
    def desc():
        return "use a fanout block on the hdacv2 board"


    def build_ctype(self):
        return build_circ_ctype({
            'type':enums.CircCmdType.USE_FANOUT.name,
            'data':{
                'fanout':{
                    'loc':self._loc.build_ctype(),
                    'inv':[
                        self._inv0.code(),
                        self._inv1.code(),
                        self._inv2.code()
                    ],
                    'in_range':self._in_range.code()
                }
            }
        })


    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,3,0,1,
                                     UseFanoutCmd.name(),
                                     index=True)
        if result.success:
            data = result.value
            return UseFanoutCmd(
                data['chip'],
                data['tile'],
                data['slice'],
                data['index'],
                in_range=data['range0'],
                inv0=data['sign0'],
                inv1=data['sign1'],
                inv2=data['sign2']
            )
        else:
            raise Exception(result.message)


    def __repr__(self):
        st = "use_fanout %d %d %d %d sgn %s %s %s rng %s" % (\
                    self.loc.chip,
                    self.loc.tile,
                    self.loc.slice,
                    self.loc.index,
                    self._inv[0].abbrev(),
                    self._inv[1].abbrev(),
                    self._inv[2].abbrev(),
                    self._in_range.abbrev())
        return st




class UseMultCmd(UseCommand):


    def __init__(self,chip,tile,slice,index,
                 in0_range=RangeType.MED,
                 in1_range=RangeType.MED,
                 out_range=RangeType.MED,
                 coeff=0,use_coeff=False,
                 inv=SignType.POS):
        UseCommand.__init__(self,
                            enums.BlockType.MULT,
                            CircLoc(chip,tile,slice,index))

        if coeff < -1.0 or coeff > 1.0:
            self.fail("value not in [-1,1]: %s" % coeff)

        assert(isinstance(inv,SignType))
        assert(isinstance(in0_range,RangeType))
        assert(isinstance(in1_range,RangeType))
        assert(isinstance(out_range,RangeType))

        self._use_coeff = use_coeff
        self._coeff = coeff
        self._in0_range = in0_range
        self._in1_range = in1_range
        self._out_range = out_range



    @staticmethod
    def desc():
        return "use a multiplier block on the hdacv2 board"

    def build_ctype(self):
        return build_circ_ctype({
            'type':enums.CircCmdType.USE_MULT.name,
            'data':{
                'mult':{
                    'loc':self._loc.build_ctype(),
                    'use_coeff':self._use_coeff,
                    'coeff':self._coeff,
                    'in0_range':self._in0_range.code(),
                    'in1_range':self._in1_range.code(),
                    'out_range':self._out_range.code()
                }
            }
        })

    @staticmethod
    def parse(args):
        return UseMultCmd._parse(args,UseMultCmd)

    @staticmethod
    def _parse(args,cls):
        result1 = parse_pattern_block(args,0,1,2,
                                      cls.name(),
                                     index=True)

        result2 = parse_pattern_block(args,0,0,3,
                                      cls.name(),
                                      index=True)

        if result1.success:
            data = result1.value
            return cls(data['chip'],data['tile'],
                              data['slice'],data['index'],
                              in0_range=data['range0'],
                              in1_range=RangeType.MED,
                              out_range=data['range1'],
                              use_coeff=True,
                              coeff=data['value0'])
        elif result2.success:
            data = result2.value
            return cls(data['chip'],data['tile'],
                              data['slice'],data['index'],
                              in0_range=data['range0'],
                              in1_range=data['range1'],
                              out_range=data['range2'],
                              use_coeff=False, coeff=0)

        elif not result1.success and not result2.success:
            msg = result1.message
            msg += "OR\n"
            msg += result2.message
            raise Exception(msg)


    @staticmethod
    def name():
        return 'use_mult'

    def __repr__(self):
        if self._use_coeff:
            st = "%s %d %d %d %d val %f rng %s %s" % (\
                                                      self.name(),
                                                      self.loc.chip,
                                                                   self.loc.tile,
                                                                   self.loc.slice,
                                                                   self.loc.index,
                                                                   self._coeff,
                                                                   self._in0_range.abbrev(),
                                                                   self._out_range.abbrev()
            )
        else:
            st = "%s %d %d %d %d rng %s %s %s" % (self.name(),
                                                  self.loc.chip,
                                                               self.loc.tile,
                                                               self.loc.slice,
                                                               self.loc.index,
                                                               self._in0_range.abbrev(),
                                                               self._in1_range.abbrev(),
                                                               self._out_range.abbrev())

        return st


class ConfigMultCmd(UseMultCmd):

    def __init__(self,chip,tile,slice,index,
                 in0_range=RangeType.MED,
                 in1_range=RangeType.MED,
                 out_range=RangeType.MED,
                 coeff=0,use_coeff=False,
                 inv=SignType.POS):
        assert(use_coeff)
        UseMultCmd.__init__(self, chip,tile,slice,index,
                 in0_range,
                 in1_range,
                 out_range,
                 coeff,
                 use_coeff,
                 inv=SignType.POS)

    @staticmethod
    def name():
        return 'config_mult'


    def priority(self):
        return Priority.NORMAL


    @staticmethod
    def parse(args):
        return UseMultCmd._parse(args,cls=ConfigMultCmd)

    def build_ctype(self):
        return build_circ_ctype({
            'type':enums.CircCmdType.CONFIG_MULT.name,
            'data':{
                'mult':{
                    'loc':self._loc.build_ctype(),
                    'use_coeff':self._use_coeff,
                    'coeff':self._coeff,
                    'in0_range':self._in0_range.code(),
                    'in1_range':self._in1_range.code(),
                    'out_range':self._out_range.code()
                }
            }
        })


class ConnectionCmd(AnalogChipCommand):

    def __init__(self,src_blk,src_loc,
                 dst_blk,dst_loc,
                 make_conn=True):
        AnalogChipCommand.__init__(self)
        assert(not src_loc is None and \
               isinstance(src_loc,CircPortLoc))
        self._src_blk = enums.BlockType(src_blk);
        self._src_loc = src_loc;
        self.test_loc(self._src_blk, self._src_loc.loc)
        assert(not src_loc is None and \
               isinstance(dst_loc,CircPortLoc))
        self._dst_blk = enums.BlockType(dst_blk);
        self._dst_loc = dst_loc;
        self.test_loc(self._dst_blk, self._dst_loc.loc)

    def build_ctype(self):
        return {
            'src_blk':self._src_blk.name,
            'src_loc':self._src_loc.build_ctype(),
            'dst_blk':self._dst_blk.name,
            'dst_loc':self._dst_loc.build_ctype()
        }

    def priority(self):
        return Priority.EARLY


    def build_identifier(self,block,ploc,is_input=False):
        rep = "%s %d %d %d" % (block.value,
                               ploc.loc.chip,
                               ploc.loc.tile,
                               ploc.loc.slice)

        if self.specify_index(block,ploc.loc):
            rep += " %d" % ploc.loc.index

        if self.specify_output_port(block) and not is_input:
            rep += " port %d" % ploc.port

        if self.specify_input_port(block) and is_input:
            rep += " port %d" % ploc.port


        return rep

    def __repr__(self):
        return "conn %s.%s <-> %s.%s" % (self._src_blk,
                                         self._src_loc,
                                         self._dst_blk,
                                         self._dst_loc)
class BreakConnCmd(ConnectionCmd):

    def __init__(self,src_blk,src_loc,
                 dst_blk,dst_loc):
        ConnectionCmd.__init__(self,src_blk,src_loc,
                               dst_blk,dst_loc,True)

    def disable(self):
        return self

    @staticmethod
    def name():
        return 'rmconn'

    @staticmethod
    def desc():
        return "make a connection on the hdacv2 board"

    def build_ctype(self):
        data = ConnectionCmd.build_ctype(self)
        return build_circ_ctype({
            'type':enums.CircCmdType.BREAK.name,
            'data':{
                'conn':data
            }
        })


    @staticmethod
    def parse(args):
        result = parse_pattern_conn(args,BreakConnCmd.name())
        if result.success:
            data = result.value
            srcloc = CircPortLoc(data['schip'],data['stile'],
                                 data['sslice'],data['sport'],
                                 data['sindex'])
            dstloc = CircPortLoc(data['dchip'],data['dtile'],
                                 data['dslice'],data['dport'],
                                 data['dindex'])


            return BrkConnCmd(
                data['sblk'],srcloc,
                data['dblk'],dstloc)

        else:
            raise Exception(result.message)


    def __repr__(self):
        src_rep = self.build_identifier(self._src_blk,
                                        self._src_loc,is_input=False)
        dest_rep = self.build_identifier(self._dst_blk,
                                         self._dst_loc,is_input=True)

        return "rmconn %s %s" % (src_rep,dest_rep)





class MakeConnCmd(ConnectionCmd):

    def __init__(self,src_blk,src_loc,
                 dst_blk,dst_loc):
        ConnectionCmd.__init__(self,src_blk,src_loc,
                               dst_blk,dst_loc,True)

    @staticmethod
    def name():
        return 'mkconn'

    @staticmethod
    def desc():
        return "make a connection on the hdacv2 board"

    def priority(self):
        return Priority.LAST

    def build_ctype(self):
        data = ConnectionCmd.build_ctype(self)
        return build_circ_ctype({
            'type':enums.CircCmdType.CONNECT.name,
            'data':{
                'conn':data
            }
        })




    @staticmethod
    def parse(args):
        result = parse_pattern_conn(args,MakeConnCmd.name())
        if result.success:
            data = result.value
            srcloc = CircPortLoc(data['schip'],data['stile'],
                                 data['sslice'],data['sport'],
                                 data['sindex'])
            dstloc = CircPortLoc(data['dchip'],data['dtile'],
                                 data['dslice'],data['dport'],
                                 data['dindex'])


            return MakeConnCmd(
                data['sblk'],srcloc,
                data['dblk'],dstloc)

        else:
            raise Exception(result.message)

    def configure(self):
        return self

    def disable(self):
        return BreakConnCmd(self._src_blk,self._src_loc,
                             self._dst_blk,self._dst_loc)


    def __repr__(self):
        src_rep = self.build_identifier(self._src_blk,
                                        self._src_loc,is_input=False)
        dest_rep = self.build_identifier(self._dst_blk,
                                         self._dst_loc,is_input=True)

        return "mkconn %s %s" % (src_rep,dest_rep)
