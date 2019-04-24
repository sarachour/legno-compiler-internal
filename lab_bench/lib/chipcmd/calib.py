import lab_bench.lib.enums as enums
from lab_bench.lib.chipcmd.data import AnalogChipCommand, CircLoc
from lab_bench.lib.chipcmd.common import *
import json

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

    FILE = "codes.txt"

    def __init__(self,blk,loc,port_type,rng):
        AnalogChipCommand.__init__(self)
        self._blk = enums.BlockType(blk)
        self._loc = loc
        self._port_type = enums.PortType(port_type)
        self._rng = RangeType.from_abbrev(rng)
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
                    'port_type': self._port_type.code(),
                    'range': self._rng.code(),
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
            return GetCodesCmd(data['blk'],loc,
                               data['port_type'],
                               data['range'])
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

    def execute_command(self,state):
        resp = ArduinoCommand.execute_command(self,state)
        datum = self._loc.to_json()
        datum['block_type'] = self._blk.value
        datum['port_type'] = self._port_type.value
        datum['scale_mode'] = self._rng.value
        datum['codes'] = self.to_key_value(resp.data(0))
        with open(GetCodesCmd.FILE, 'a') as fh:
            fh.write(json.dumps(datum))
            fh.write("\n")
        return True


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

