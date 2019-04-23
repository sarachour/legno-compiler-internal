import lab_bench.lib.enums as enums
from lab_bench.lib.chipcmd.data import AnalogChipCommand, CircLoc
from lab_bench.lib.chipcmd.common import *


class MeasureCmd(AnalogChipCommand):

    def __init__(self,loc):
        pass

    @staticmethod
    def name():
        return 'measure'


class SetCodesCmd(AnalogChipCommand):

    def __init__(self,blk,loc):
        AnalogChipCommand.__init__(self)
        self._blk = enums.BlockType(blk);
        self._loc = loc;
        self.test_loc(self._blk, self._loc.loc)
        assert(not loc is None and \
               isinstance(loc,CircPortLoc))


    @staticmethod
    def name():
        return 'set_codes'


class GetCodesCmd(AnalogChipCommand):

    def __init__(self,blk,loc):
        AnalogChipCommand.__init__(self)
        self._blk = enums.BlockType(blk);
        self._loc = loc;
        self.test_loc(self._blk, self._loc.loc)
        assert(not loc is None and \
               isinstance(loc,CircPortLoc))

    @staticmethod
    def name():
        return 'get_codes'

    @staticmethod
    def desc():
        return "get the bias/nmos/pmos codes for the chip"


    def build_ctype(self):
        return build_circ_ctype({
            'type':enums.CircCmdType.GET_CODES.name,
            'data':{
                'codes':{
                    'blk': self._blk.name,
                    'loc': self._loc.build_ctype(),
                    'keyvals': [0]*10
                }
            }
        })


    @staticmethod
    def parse(args):
        result = parse_pattern_port(args,GetCodesCmd.name())
        if result.success:
            data = result.value
            loc = CircPortLoc(data['chip'],data['tile'],
                                 data['slice'],data['port'],
                                 data['index'])
            return GetCodesCmd(data['blk'],loc)
        else:
            print(result.message)
            raise Exception("<parse_failure>: %s" % args)


    def __repr__(self):
        return "get_codes %s" % self._loc


class CalibrateCmd(AnalogChipCommand):

    def __init__(self,chip,tile,slice):
        AnalogChipCommand.__init__(self)
        self._loc = CircLoc(chip,tile,slice)
        self.test_loc(enums.BlockType.NONE,self._loc)

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

    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,0,0,0,
                                      CalibrateCmd.name(),
                                      index=False)
        if result.success:
            data = result.value
            return CalibrateCmd(data['chip'],data['tile'],
                                data['slice'])
        else:
            print(result.message)
            raise Exception("<parse_failure>: %s" % args)

    def __repr__(self):
        return "calib %s" % self._loc

