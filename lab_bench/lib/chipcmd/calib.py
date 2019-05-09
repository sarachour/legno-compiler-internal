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
        statebuf = self._state.build_ctype()
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
        typ = cstructs.state_t()
        obj = typ.parse(data)
        if self._blk == enums.BlockType.FANOUT:
            st = chipstate.FanoutBlockState(self._loc,obj.fanout)
            print(obj.fanout)
            env.state_db.put(st)
        elif self._blk == enums.BlockType.INTEG:
            st = chipstate.IntegBlockState(self._loc,obj.integ)
            print(obj.integ)
            env.state_db.put(st)
        elif self._blk == enums.BlockType.MULT:
            st = chipstate.MultBlockState(self._loc,obj.mult)
            print(obj.mult)
            env.state_db.put(st)
        elif self._blk == enums.BlockType.DAC:
            st = chipstate.DacBlockState(self._loc,obj.dac)
            print(obj.dac)
            env.state_db.put(st)
        elif self._blk == enums.BlockType.ADC:
            st = chipstate.AdcBlockState(self._loc,obj.adc)
            print(obj.adc)
            env.state_db.put(st)
        else:
            raise Exception("unimplemented block : <%s>" \
                            % self._blk.name)
        return True


    def __repr__(self):
        return "get_codes %s" % self._loc


class CalibrateCmd(AnalogChipCommand):

    def __init__(self,blk,chip,tile,slice,index=None):
        AnalogChipCommand.__init__(self)
        self._loc = CircLoc(chip,tile,slice,index=0 if index is None \
                            else index)
        self._blk = enums.BlockType(blk)
        self.test_loc(self._blk,self._loc)

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
                    'loc': loc_type
                }
            }
        })

    @staticmethod
    def parse(args):
        result = parse_pattern_block_loc(args,
                                      CalibrateCmd.name())
        if result.success:
            data = result.value
            return CalibrateCmd(data["blk"],
                                data['chip'],
                                data['tile'],
                                data['slice'],
                                data['index'])
        else:
            print(result.message)
            raise Exception("<parse_failure>: %s" % args)

    def __repr__(self):
        return "calib %s" % self._loc

