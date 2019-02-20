import lab_bench.lib.enums as enums
from lab_bench.lib.chipcmd.common import *
from lab_bench.lib.chipcmd.data import *
from lab_bench.lib.chipcmd.calib import CalibrateCmd
from lab_bench.lib.chipcmd.disable import DisableCmd
import lab_bench.lib.util as util
import numpy as np
from enum import Enum
import construct
import math

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



class UseFanoutCmd(UseCommand):


    def __init__(self,chip,tile,slice,index,
                 in_range,
                 inv0=False,inv1=False,inv2=False):

        assert(isinstance(inv0, SignType))
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

