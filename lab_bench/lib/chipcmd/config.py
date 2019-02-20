from lib.chipcmd.use import UseDACCmd, UseIntegCmd,UseMultCmd
from lib.chipcmd.data import *
from lib.chipcmd.common import *

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


