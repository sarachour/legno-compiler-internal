import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums

def parse_pattern_conn(args,name):
    line = " ".join(args)

    cmd = "{sblk:w} {schip:d} {stile:d} {sslice:d} {sindex:d} "
    cmd += "{sport:d} "
    cmd += "{dblk:w} {dchip:d} {dtile:d} {dslice:d} {dindex:d}"
    cmd += "{dport:d} "

    result = parselib.parse(cmd,line)
    if result is None:
        print("usage: %s %s" % (name,cmd))
        return None

    return result

def parse_pattern_block(args,n_outs,n_consts,name,index=False):
    line = " ".join(args)
    signd = {'+':False,'-':True}
    cmd = "{chip:d} {tile:d} {slice:d} "
    if index:
        cmd += "{index:d} "
    cmd += ' '.join(map(lambda idx: "{sign%d}" % idx,
                        range(0,n_outs)))
    cmd += ' '.join(map(lambda idx: "{value%d:g}" % idx,
                        range(0,n_consts)))

    result = parselib.parse(cmd,line)
    if result is None:
        print("usage: %s %s" % (name,cmd))
        return None

    for idx in range(0,n_outs):
        key = 'sign%d' % idx
        result[key] = signd[result[key]]

    return result

class CircLoc:

    def __init__(self,chip,tile,slice,index=None):
        self.chip = chip;
        self.tile = tile;
        self.slice = slice;
        self.index = index;

class CircPortLoc:

    def __init__(self,chip,tile,slice,port,index=None):
        self.loc = CircLoc(chip,tile,slice,port,index)
        self.port = port


class Command:

    def __init__(self):
        pass

    def tostr(self):
        raise NotImplementedError

class ArduinoCommand:

    def __init__(self,typ=cstructs.cmd_t()):
        self._c_type = typ

    def build_ctype(self):
        raise NotImplementedError

    def execute(self,state):
        data = self.build_ctype()
        cdata = self._c_type.build(data)
        state.arduino.write(cdata)

class UseCommand(ArduinoCommand):

    def __init__(self,block,loc):
        ArduinoCommand.__init__(self)
        self._loc = loc
        self._block = block

    def calibrate(self):
        return CalibrateCommand(
            self._loc.chip,
            self._loc.tile,
            self._loc.slice)

    def disable(self):
         return DisableCommand(
             self._block,
             self._loc.chip,
             self._loc.tile,
             self._loc.slice,
             self._loc.index)

class UseDacCmd(UseCommand):


    def __init__(self,chip,tile,slice,value,inv=False):
        UseCommand.__init__(self,
                            enums.BlockType.DAC,
                            CircLoc(chip,tile,slice))
        self._value = value
        self._inv = inv

    @staticmethod
    def desc():
        return "use a constant dac block on the hdacv2 board"


    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,1,1,
                                     UseDacCmd.name())
        if not result is None:
            return UseDacCmd(
                result['chip'],
                result['tile'],
                result['slice'],
                result['value0'],
                inv=result['sign0']
            )

    @staticmethod
    def name():
        return 'use_dac'


class UseIntegCmd(UseCommand):


    def __init__(self,chip,tile,slice,value,inv=False):
        UseCommand.__init__(self,
                            enums.BlockType.INTEG,
                            CircLoc(chip,tile,slice))

        self._value = value
        self._inv = inv

    @staticmethod
    def desc():
        return "use a integrator block on the hdacv2 board"


    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,1,1,UseIntegCmd.name())
        if not result is None:
            return UseIntegCmd(
                result['chip'],
                result['tile'],
                result['slice'],
                result['value0'],
                inv=result['sign0']
            )

    @staticmethod
    def name():
        return 'use_integ'


class UseFanoutCmd(ArduinoCommand):


    def __init__(self,chip,tile,slice,index,
                 inv0=False,inv1=False,inv2=False):
        UseCommand.__init__(self,
                            enums.BlockType.FANOUT,
                            CircLoc(chip,tile,slice,index))

        self._inv = [inv0,inv1,inv2]

    @staticmethod
    def desc():
        return "use a fanout block on the hdacv2 board"


    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,3,0,UseFanoutCmd.name(),
                                     index=True)
        if not result is None:
            return UseFanoutCmd(
                result['chip'],
                result['tile'],
                result['slice'],
                result['index'],
                inv0=result['sign0'],
                inv1=result['sign1'],
                inv2=result['sign2']
            )

    @staticmethod
    def name():
        return 'use_fan'

class UseMultCmd(UseCommand):


    def __init__(self,chip,tile,slice,index,
                 coeff=0,use_coeff=False,inv=False):
        UseCommand.__init__(self,
                            enums.BlockType.MULT,
                            CircLoc(chip,tile,slice,index))

        self._value = value
        self._inv = inv

    @staticmethod
    def desc():
        return "use a multiplier block on the hdacv2 board"


    @staticmethod
    def parse(args):
        result1 = parse_pattern_block(args,1,1,
                                      UseMultCmd.name(),
                                     index=True)

        result2 = parse_pattern_block(args,1,0,
                                      UseMultCmd.name(),
                                      index=True)

        if not result1 is None:
            return UseMultCmd(result['chip'],result['tile'],
                              result['slice'],result['index'],
                              use_coeff=True,
                              coeff=result['value0'],
                              inv=result['sign0'])
        elif not result2 is None:
             return UseMultCmd(result['chip'],result['tile'],
                              result['slice'],result['index'],
                              use_coeff=False, coeff=0,
                              inv=result['sign0'])

        else:
            return None

    @staticmethod
    def name():
        return 'use_mult'



class DisableCmd(ArduinoCommand):

    def __init__(self,block,chip,tile,slice,index=None):
        ArduinoCommand.__init__(self)
        self._block = block;
        self._loc = CircLoc(chip,tile,slice,index)


    @staticmethod
    def name():
        return 'disable'

    @staticmethod
    def desc():
        return "disable a block on the hdacv2 board"

    def parse(args):
        result1 = parse_pattern_block(args[1:],0,0,
                                      DisableCmd.name(),
                                      index=True)
        result2 = parse_pattern_block(args[1:],0,0,
                                      DisableCmd.name(),
                                      index=False)

        if not result1 is None:
            return DisableCmd(args[0],
                              result['block'],
                              result['chip'],
                              result['tile'],
                              result['slice'],
                              result['index'])
        elif not result2 is None:
            return DisableCmd(args[0],
                              result['block'],
                              result['chip'],
                              result['tile'],
                              result['slice'])

class CalibrateCmd(ArduinoCommand):

    def __init__(self,chip,tile,slice):
        ArduinoCommand.__init__(self)
        self._loc = CircLoc(chip,tile,slice)


    @staticmethod
    def name():
        return 'calib'

    @staticmethod
    def desc():
        return "calibrate a slice on the hdacv2 board"

    def parse(args):
        line = " ".join(args)
        result = parse_pattern_block(args,0,0,
                                      CalibrateCmd.name(),
                                      index=False)
        return CalibrateCmd(result['chip'],result['tile'],
                            result['slice'])

class ConnectionCmd(ArduinoCommand):

    def __init__(self,src_blk,src_loc,
                 dst_blk,dst_loc,
                 make_conn=True):
        assert(isinstance(src_loc,CircPortLoc))
        self._src_blk = src_blk;
        self._src_loc = src_loc;
        assert(isinstance(dst_loc,CircPortLoc))
        self._dst_blk = dst_blk;
        self._dst_loc = dst_loc;

class BreakConnCmd(ConnectionCmd):

    def __init__(self,src_blk,src_loc,
                 dst_blk,dst_loc):
        ConnectionCmd.__init__(src_blk,src_loc,
                               dst_blk,dst_loc,True)

    @staticmethod
    def name():
        return 'rmconn'

    @staticmethod
    def desc():
        return "make a connection on the hdacv2 board"

    @staticmethod
    def parse(args):
        result = parse_pattern_conn(args,BreakConnCmd.name())
        if not result is None:
            srcloc = ChipPortLoc(result['schip'],result['stile'],
                                 result['sslice'],result['sport'],
                                 result['sindex'])
            dstloc = ChipPortLoc(result['dchip'],result['dtile'],
                                 result['dslice'],result['dport'],
                                 result['dindex'])


            return ConnectionCmd(
                result['sblk'],srcloc,
                result['dblk'],dstloc,
                make_conn=False)



class MakeConnCmd(ConnectionCmd):

    def __init__(self,src_blk,src_loc,
                 dst_blk,dst_loc):
        ConnectionCmd.__init__(src_blk,src_loc,
                               dst_blk,dst_loc,True)

    @staticmethod
    def name():
        return 'mkconn'

    @staticmethod
    def desc():
        return "break a connection on the hdacv2 board"

    @staticmethod
    def parse(args):
        result = parse_pattern_conn(args,MakeConnCmd.name())
        if not result is None:
            srcloc = ChipPortLoc(result['schip'],result['stile'],
                                 result['sslice'],result['sport'],
                                 result['sindex'])
            dstloc = ChipPortLoc(result['dchip'],result['dtile'],
                                 result['dslice'],result['dport'],
                                 result['dindex'])


            return ConnectionCmd(
                result['sblk'],srcloc,
                result['dblk'],dstloc,
                make_conn=True)


    def break_conn(self):
        return BreakConnectionCmd(self._src_blk,self._src_loc,
                             self._dst_blk,self._dst_loc)


COMMANDS = [
    UseDacCmd,
    UseIntegCmd,
    UseMultCmd,
    UseFanoutCmd,
    MakeConnCmd
]
def parse(line):
    args = line.strip().split()
    if len(args) == 0:
        return None

    for cmd in COMMANDS:
        if args[0] == cmd.name():
            obj = cmd.parse(args[1:])
            return obj

    if args[0] == 'help':
        for cmd in COMMANDS:
            print("%s: %s" % (cmd.name(),cmd.desc()))


    return None

