from enum import Enum
from lab_bench.lib.base_command import ArduinoCommand
import lab_bench.lib.cstructs as cstructs
import lab_bench.lib.enums as enums

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
            return 2
        elif self == LUTSourceType.ADC0:
            return 0
        elif self == LUTSourceType.ADC1:
            return 1
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
        yield RangeType.HIGH
        yield RangeType.MED
        yield RangeType.LOW

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

    @staticmethod
    def has(v):
      assert(isinstance(v,Enum))
      for name in RangeType.option_names():
        if v.name == name:
          return True
      return False

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
            return 2
        elif self == RangeType.HIGH:
            return 0
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
    def has(v):
      assert(isinstance(v,Enum))
      for name in SignType.option_names():
        if v.name == name:
          return True
      return False


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


class CircLoc:

    def __init__(self,chip,tile,slice,index=None):
        self.chip = chip;
        self.tile = tile;
        self.slice = slice;
        self.index = index;

    def to_json(self):
        return {
            'chip': self.chip,
            'tile': self.tile,
            'slice': self.slice,
            'index': self.index
        }

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

    def to_json(self):
        return {
            'loc': self.loc.to_json(),
            'port_id': self.port
        }

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

