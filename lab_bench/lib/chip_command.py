import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
from lib.base_command import Command,ArduinoCommand
import lib.util as util
import numpy as np
from enum import Enum

class RangeType(str,Enum):
    MED = 'medium'
    HIGH = 'high'
    LOW = 'low'

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
        return self.abbrev()

class SignType(str,Enum):
    POS = 'pos'
    NEG = 'neg'

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
                cmd = src + " " + dst
                result = parselib.parse(cmd,line)

    if result is None:
        print("usage: %s %s" % (name,cmd))
        return None

    result = dict(result.named.items())
    if not 'sindex' in result:
        result['sindex'] = None
    if not 'dindex' in result:
        result['dindex'] = None
    if not 'sport' in result:
        result['sport'] = None
    if not 'dport' in result:
        result['dport'] = None

    return result

def parse_pattern_block(args,n_signs,n_consts,n_range_codes, \
                        name,index=False,debug=False):
    line = " ".join(args)
    SIGND = {'+':False,'-':True}
    DEBUG = {'debug':True,'prod':False}
    RANGED = {
        'm':PortRangeType.MED,
        'l':PortRangeType.LOW,
        'h':PortRangeType.HIGH
    }
    cmd = "{chip:d} {tile:d} {slice:d}"
    if index:
        cmd += " {index:d}"
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

    cmd = cmd.strip()
    result = parselib.parse(cmd,line)
    if result is None:
        print("usage: <%s:%s>" % (name,cmd))
        print("line: <%s>" % line)
        return None

    result = dict(result.named.items())
    for idx in range(0,n_signs):
        key = 'sign%d' % idx
        if not result[key] in SIGND:
            print("unknown sign: <%s>" % result[key])
            return None

        result[key] = SignType.from_abbrev(result[key])

    for idx in range(0,n_range_codes):
        key = 'range%d' % idx
        if not result[key] in RANGED:
            print("unknown sign: <%s>" % result[key])
            return None

        result[key] = RangeType.from_abbrev(result[key])

    if debug:
        result['debug'] = DEBUG[result['debug']]

    return result


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
        if not loc.chip in range(0,2):
            self.fail("unknown chip <%d>" % loc.chip)
        if not loc.tile in range(0,4):
            self.fail("unknown tile <%d>" % loc.tile)
        if not loc.slice in range(0,4):
            self.fail("unknown slice <%d>" % loc.slice)
        if not loc.index is None and \
           not loc.index in range(0,2):
            self.fail("unknown index <%s>" % loc.index)

        if (block == enums.BlockType.FANOUT) \
            or (block == enums.BlockType.TILE_INPUT) \
            or (block == enums.BlockType.TILE_OUTPUT) \
            or (block == enums.BlockType.MULT):
            indices = {
                enums.BlockType.FANOUT: range(0,2),
                enums.BlockType.MULT: range(0,2),
                enums.BlockType.TILE_INPUT: range(0,4),
                enums.BlockType.TILE_OUTPUT: range(0,4)
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

    def preexec(self):
        return None

    def postexec(self):
        return None

    def calibrate(self):
        return None

    def disable(self):
        return None

    def configure(self):
        return None

    def execute_command(self,state):
        raise Exception("cannot directly execute analog chip command")

    def apply(self,state):
        if state.dummy:
            return

        resp = ArduinoCommand.execute_command(self,state)
        print("cmd> %s" % resp)
        line = state.arduino.readline()
        print("resp> %s" % line)
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
                    'circ_loc':self._loc.build
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
        line = " ".join(args)
        result = parse_pattern_block(args,0,0,0,
                                      CalibrateCmd.name(),
                                      index=False)
        return CalibrateCmd(result['chip'],result['tile'],
                            result['slice'])

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

class UseDACCmd(UseCommand):

    def __init__(self,chip,tile,slice,value,inv=False):
        UseCommand.__init__(self,
                            enums.BlockType.DAC,
                            CircLoc(chip,tile,slice))

        if value < -1.0 or value > 1.0:
            self.fail("value not in [-1,1]: %s" % value)
        if not self._loc.index is None:
            self.fail("dac has no index <%d>" % loc.index)

        self._value = value
        self._inv = inv

    @staticmethod
    def desc():
        return "use a constant dac block on the hdacv2 board"


    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,1,1,1,
                                     UseDACCmd.name())
        if not result is None:
            return UseDACCmd(
                result['chip'],
                result['tile'],
                result['slice'],
                result['value0'],
                inv=result['sign0'],
                out_range=result['range0']
            )

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
                    'inv':self._inv.code(),
                    'out_range':self._out_range.code()
                }
            }
        })

    @staticmethod
    def name():
        return 'use_dac'

    def __repr__(self):
        st = "use_dac %s %s %s sgn %s val %s rng %s" % \
              (self.loc.chip,self.loc.tile, \
               self.loc.slice,
               self._inv.abbrev(),
               self._value,
               self._out_range.abbrev())
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
        if not result is None:
            return GetIntegStatusCmd(
                result['chip'],
                result['tile'],
                result['slice']
            )


    def preexec(self):
        return self

    def postexec(self):
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
        oflow_val = int(state.arduino.readline())
        oflow = True if oflow_val == 1 else False
        print("overflow_val: %s" % oflow_val)
        state.set_overflow(handle, oflow)



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
        if init_cond < -1.0 or init_cond > 1.0:
            self.fail("init_cond not in [-1,1]: %s" % init_cond)

        self._init_cond = init_cond
        self._inv = inv
        if in_range == PortRangeType.HIGH and \
           out_range == PortRangeType.LOW:
            raise Exception("incompatible: high input and low output")
        elif in_range == PortRangeType.LOW and \
             out_range == PortRangeType.HIGH:
            raise Exception("incompatible: high input and low output")

        self._in_range = in_range
        self._out_range = out_range
        self._debug = debug


    @staticmethod
    def desc():
        return "use a integrator block on the hdacv2 board"


    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,1,1,2,
                                     UseIntegCmd.name(),
                                     debug=True)
        if not result is None:
            return UseIntegCmd(
                result['chip'],
                result['tile'],
                result['slice'],
                result['value0'],
                inv=result['sign0'],
                in_range=result['range0'],
                out_range=result['range1'],
                debug=result['debug']
            )

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
        fmtstr = "use_integ %d %d %d sgn %s val %f rng %s %s %s"
        st = fmtstr % (self.loc.chip, \
                       self.loc.tile, \
                       self.loc.slice, \
                       self._inv.abbrev(),
                       self._init_cond,
                       self._in_range.abbrev(),
                       self._out_range.abbrev(),
                       "debug" if self._debug else "prod")
        return st




class UseFanoutCmd(UseCommand):


    def __init__(self,chip,tile,slice,index,
                 in_range,
                 inv0=False,inv1=False,inv2=False):
        UseCommand.__init__(self,
                            enums.BlockType.FANOUT,
                            CircLoc(chip,tile,slice,index))

        self._inv = [inv0,inv1,inv2]
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
                    'inv':self._inv.code(),
                    'in_range':self._in_range.code()
                }
            }
        })


    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,3,0,1,
                                     UseFanoutCmd.name(),
                                     index=True)
        if not result is None:
            return UseFanoutCmd(
                result['chip'],
                result['tile'],
                result['slice'],
                result['index'],
                in_range=result['range0'],
                inv0=result['sign0'],
                inv1=result['sign1'],
                inv2=result['sign2']
            )

    def __repr__(self):
        st = "use_fanout %d %d %d %d sgn %s %s %s rng %s" % (self.loc.chip,
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
                 in0_range,in1_range,out_range,
                 coeff=0,use_coeff=False,inv=False):
        UseCommand.__init__(self,
                            enums.BlockType.MULT,
                            CircLoc(chip,tile,slice,index))

        if coeff < -1.0 or coeff > 1.0:
            self.fail("value not in [-1,1]: %s" % coeff)

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
        result1 = parse_pattern_block(args,0,1,2,
                                      UseMultCmd.name(),
                                     index=True)

        result2 = parse_pattern_block(args,0,0,3,
                                      UseMultCmd.name(),
                                      index=True)

        if not result1 is None:
            return UseMultCmd(result1['chip'],result1['tile'],
                              result1['slice'],result1['index'],
                              in0_range=result1['range0'],
                              in1_range=RangeType.MED,
                              out_range=result1['range1'],
                              use_coeff=True,
                              inv=result2['sign0'],
                              coeff=result1['value0'])
        elif not result2 is None:
            return UseMultCmd(result2['chip'],result2['tile'],
                              result2['slice'],result2['index'],
                              in0_range=result2['range0'],
                              in1_range=result2['range1'],
                              out_range=result2['range2'],
                              inv=result2['sign0'],
                              use_coeff=False, coeff=0)

        else:
            return None

    @staticmethod
    def name():
        return 'use_mult'

    def __repr__(self):
        if self._use_coeff:
            st = "use_mult %d %d %d %d val %f rng %s %s" % (self.loc.chip,
                                                                   self.loc.tile,
                                                                   self.loc.slice,
                                                                   self.loc.index,
                                                                   self._coeff,
                                                                   self._in0_range.abbrev(),
                                                                   self._out_range.abbrev()
            )
        else:
            st = "use_mult %d %d %d %d rng %s %s %s" % (self.loc.chip,
                                                               self.loc.tile,
                                                               self.loc.slice,
                                                               self.loc.index,
                                                               self._in0_range.abbrev(),
                                                               self._in1_range.abbrev(),
                                                               self._out_range.abbrev())

        return st


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
        if not result is None:
            srcloc = CircPortLoc(result['schip'],result['stile'],
                                 result['sslice'],result['sport'],
                                 result['sindex'])
            dstloc = CircPortLoc(result['dchip'],result['dtile'],
                                 result['dslice'],result['dport'],
                                 result['dindex'])


            return BrkConnCmd(
                result['sblk'],srcloc,
                result['dblk'],dstloc)




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
        if not result is None:
            srcloc = CircPortLoc(result['schip'],result['stile'],
                                 result['sslice'],result['sport'],
                                 result['sindex'])
            dstloc = CircPortLoc(result['dchip'],result['dtile'],
                                 result['dslice'],result['dport'],
                                 result['dindex'])


            return MakeConnCmd(
                result['sblk'],srcloc,
                result['dblk'],dstloc)


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
