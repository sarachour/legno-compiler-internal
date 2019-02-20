import lab_bench.lib.enums as enums
from lab_bench.lib.chipcmd.data import AnalogChipCommand, CircLoc
from lab_bench.lib.chipcmd.common import *


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

