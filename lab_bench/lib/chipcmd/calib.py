import lab_bench.lib.enums as enums
import lab_bench.lib.cstructs as cstructs
from lab_bench.lib.base_command import AnalogChipCommand
from lab_bench.lib.chipcmd.data import CircLoc
from lab_bench.lib.chipcmd.common import *
import lab_bench.lib.chipcmd.state as chipstate
import json

class MeasureCmd(AnalogChipCommand):

    def __init__(self,loc):
        pass

    @staticmethod
    def name():
        return 'measure'


class SetStateCmd(AnalogChipCommand):

    def __init__(self,blk,loc,state):
        AnalogChipCommand.__init__(self)
        self._blk = enums.BlockType(blk);
        assert(isinstance(loc, CircLoc) and loc.index != None)
        self._loc = loc;
        self._state = state
        self.test_loc(self._blk, self._loc)
        assert(not loc is None and \
               isinstance(loc,CircLoc))



    def build_ctype(self):
        statebuf = self._state.to_cstruct()
        len(statebuf)
        padding = bytes([0]*(64-len(statebuf)))
        buf = statebuf+padding
        print(self._loc)
        return build_circ_ctype({
            'type':enums.CircCmdType.SET_STATE.name,
            'data':{
                'state':{
                    'blk': self._blk.name,
                    'loc': self._loc.build_ctype(),
                    'data': buf
                }
            }
        })
    @staticmethod
    def name():
        return 'set_codes'


class GetStateCmd(AnalogChipCommand):


    def __init__(self,blk,chip,tile,slce,index=None):
        AnalogChipCommand.__init__(self)
        self._blk = enums.BlockType(blk)
        self._loc = CircLoc(chip,tile,slce,index=0 if index is None \
                            else index)

        self.test_loc(self._blk, self._loc)

    @staticmethod
    def name():
        return 'get_state'

    @staticmethod
    def desc():
        return "get the bias/nmos/pmos codes for the chip"


    def build_ctype(self):
        return build_circ_ctype({
            'type':enums.CircCmdType.GET_STATE.name,
            'data':{
                'state':{
                    'blk': self._blk.name,
                    'loc': self._loc.build_ctype(),
                    'data': [0]*64
                }
            }
        })


    @staticmethod
    def parse(args):
        result = parse_pattern_block_loc(args,GetStateCmd.name())
        if result.success:
            data = result.value
            return GetStateCmd(data['blk'],
                               data['chip'],
                               data['tile'],
                               data['slice'],
                               data['index'])

        else:
            print(result.message)
            raise Exception("<parse_failure>: %s" % args)



    def to_key_value(self,array):
        i = 0;
        data = {}
        print("# els: %d" % len(array))
        while i < len(array):
            key = enums.CodeType.from_code(array[i])
            if key == enums.CodeType.CODE_END:
                return data

            value = array[i+1]
            assert(not key.value in data)
            data[key.value] = value
            i += 2;

        raise Exception("no terminator")

    def execute_command(self,env):
        resp = ArduinoCommand.execute_command(self,env)
        datum = self._loc.to_json()
        datum['block_type'] = self._blk.value
        data = bytes(resp.data(0)[1:])
        st = chipstate.BlockState \
                      .toplevel_from_cstruct(self._blk,
                                             self._loc,
                                             data)
        env.state_db.put(st)
        return True


    def __repr__(self):
        return "get_codes %s" % self._loc


class CalibrateCmd(AnalogChipCommand):

    def __init__(self,blk,chip,tile,slice,index=None,max_error=0.01):
        AnalogChipCommand.__init__(self)
        self._loc = CircLoc(chip,tile,slice,index=0 if index is None \
                            else index)
        self._blk = enums.BlockType(blk)
        self.test_loc(self._blk,self._loc)
        self._max_error = max_error

    @staticmethod
    def name():
        return 'calibrate'

    @staticmethod
    def desc():
        return "calibrate a slice on the hdacv2 board"

    def build_ctype(self):
        loc_type = self._loc.build_ctype()
        print(loc_type)
        return build_circ_ctype({
            'type':enums.CircCmdType.CALIBRATE.name,
            'data':{
                'calib':{
                    'blk': self._blk.code(),
                    'loc': loc_type,
                    'max_error': self._max_error
                }
            }
        })

    @staticmethod
    def parse(args):
        result = parse_pattern_block_loc(args,
                                         CalibrateCmd.name(),
                                         max_error=True)
        if result.success:
            data = result.value
            return CalibrateCmd(data["blk"],
                                data['chip'],
                                data['tile'],
                                data['slice'],
                                data['index'],
                                data['max_error'])
        else:
            print(result.message)
            raise Exception("<parse_failure>: %s" % args)

    def execute_command(self,env):
        resp = ArduinoCommand.execute_command(self,env)
        datum = self._loc.to_json()
        datum['block_type'] = self._blk.value
        success = BoolType.from_code(resp.data(0)[1]).boolean()
        print("success=%s" % success)
        data = bytes(resp.data(0)[2:])
        st = chipstate.BlockState \
                      .toplevel_from_cstruct(self._blk,
                                             self._loc,
                                             data)
        env.state_db.put(st,success=success,max_error=self._max_error)
        return True


    def __repr__(self):
        return "calib %s" % self._loc

