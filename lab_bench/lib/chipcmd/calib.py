import lab_bench.lib.enums as enums
import lab_bench.lib.cstructs as cstructs
from lab_bench.lib.base_command import AnalogChipCommand
from lab_bench.lib.chipcmd.data import CircLoc
from lab_bench.lib.chipcmd.common import *
import lab_bench.lib.chipcmd.state as chipstate
import json
import struct

def from_float16(val):
    nbits_exp = 6
    if val == 0:
        return 0.0

    ff = val&0x8000;
    oldexp = ((val&0x7FFF)>>(15-nbits_exp))
    bias = (1<<(nbits_exp-1))-1
    ff |= ((oldexp-bias+127)<<23);
    mantissa_mask=(0xFFFF>>(nbits_exp+1))
    ff |= ((val&mantissa_mask)<<(23-(15-nbits_exp)));

    ffstr = struct.pack('>l', ff)
    ff_float = struct.unpack('>f', ffstr)[0]
    #print("val=%d hex=%x float=%f" % (val, ff, ff_float))
    return ff_float

class CharacterizeCmd(AnalogChipCommand):

    def __init__(self,blk,chip,tile,slce,index=None,targeted=BoolType.TRUE):
        AnalogChipCommand.__init__(self)
        self._blk = enums.BlockType(blk)
        self._loc = CircLoc(chip,tile,slce,index=0 if index is None \
                            else index)

        self._targeted = targeted
        self.test_loc(self._blk, self._loc)

    @staticmethod
    def name():
        return 'profile'

    def build_ctype(self):
        loc_type = self._loc.build_ctype()
        print(loc_type)
        return build_circ_ctype({
            'type':enums.CircCmdType.CHARACTERIZE.name,
            'data':{
                'calib':{
                    'blk': self._blk.code(),
                    'loc': loc_type,
                    'max_error': 0.0,
                    'targeted': BoolType.from_bool(self._targeted).code()
                }
            }
        })

    def insert_result(self,env,resp):
        state_size = int(resp.data(0)[0])
        result_size = int(resp.data(0)[1])
        base = 2
        state_data = bytes(resp.data(0)[base:(base+state_size)])
        result_data = bytes(resp.data(0)[(base+state_size):])
        print(state_size,len(state_data))
        print(result_size,len(result_data))
        st = chipstate.BlockState \
                      .toplevel_from_cstruct(self._blk,
                                             self._loc,
                                             state_data,
                                             self._targeted)
        result = cstructs.profile_t() \
                         .parse(result_data);

        profile = []
        print("==== %d TRIALS ====" % result.size)
        for i in range(0,result.size):
            bias = from_float16(result.bias[i])
            noise = from_float16(result.noise[i])
            out = from_float16(result.output[i])
            in0 = from_float16(result.input0[i])
            in1 = from_float16(result.input1[i])
            port = enums.PortName.from_code(result.port[i])
            profile.append((port,out,in0,in1,bias,noise))
            print("TRIAL %s out=%f in0=%f in1=%f bias=%f noise=%f (var)" \
                  % (port,out,in0,in1,bias,noise))
        #FIXME save cali
        entry = env.state_db.get(st.key)
        env.state_db.put(st,entry.targeted,
                         profile=profile,
                         success=entry.success,
                         max_error=entry.tolerance)
        return True


    def execute_command(self,env):
        resp = ArduinoCommand.execute_command(self,env)
        self.insert_result(env,resp);

    @staticmethod
    def parse(args):
        result = parse_pattern_block_loc(args,CharacterizeCmd.name(),
                                         targeted=True)
        if result.success:
            data = result.value
            return CharacterizeCmd(data['blk'],
                                   data['chip'],
                                   data['tile'],
                                   data['slice'],
                                   data['index'],
                                   targeted=data['targeted'])

        else:
            print(result.message)
            raise Exception("<parse_failure>: %s" % args)





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
        padding = bytes([0]*(64-len(statebuf)))
        buf = statebuf+padding
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


    def __init__(self,blk,chip,tile,slce,index=None,targeted=True):
        AnalogChipCommand.__init__(self)
        self._blk = enums.BlockType(blk)
        self._loc = CircLoc(chip,tile,slce,index=0 if index is None \
                            else index)

        self.test_loc(self._blk, self._loc)
        self._targeted = targeted

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
                                             data,
                                             targeted=self._targeted)
        env.state_db.put(st)
        return True


    def __repr__(self):
        return "get_codes %s" % self._loc


class CalibrateCmd(AnalogChipCommand):

    def __init__(self,blk,chip,tile,slice,index=None,max_error=0.01,
                 targeted=True):
        AnalogChipCommand.__init__(self)
        self._loc = CircLoc(chip,tile,slice,index=0 if index is None \
                            else index)
        self._blk = enums.BlockType(blk)
        self.test_loc(self._blk,self._loc)
        self._max_error = max_error
        self._targeted = targeted

    @staticmethod
    def name():
        return 'calibrate'

    @staticmethod
    def desc():
        return "calibrate a slice on the hdacv2 board"

    def build_ctype(self):
        loc_type = self._loc.build_ctype()
        return build_circ_ctype({
            'type':enums.CircCmdType.CALIBRATE.name,
            'data':{
                'calib':{
                    'blk': self._blk.code(),
                    'loc': loc_type,
                    'max_error': self._max_error,
                    'targeted': BoolType.from_bool(self._targeted).code()
                }
            }
        })

    @staticmethod
    def parse(args):
        result = parse_pattern_block_loc(args,
                                         CalibrateCmd.name(),
                                         max_error=True,
                                         targeted=self._targeted)
        if result.success:
            data = result.value
            return CalibrateCmd(data["blk"],
                                data['chip'],
                                data['tile'],
                                data['slice'],
                                data['index'],
                                data['max_error'],
                                data['targeted'])
        else:
            print(result.message)
            raise Exception("<parse_failure>: %s" % args)

    def execute_command(self,env):
        resp = ArduinoCommand.execute_command(self,env)
        datum = self._loc.to_json()
        datum['block_type'] = self._blk.value
        state_size = int(resp.data(0)[1]);
        success = BoolType.from_code(resp.data(0)[1]).boolean()
        print("success=%s" % success)
        base=2
        data = bytes(resp.data(0)[base:])
        st = chipstate.BlockState \
                      .toplevel_from_cstruct(self._blk,
                                             self._loc,
                                             data,
                                             targeted=self._targeted)
        env.state_db.put(st,self._targeted,
                         success=success,max_error=self._max_error)
        return success


    def __repr__(self):
        return "calib %s" % self._loc

