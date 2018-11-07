import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
from lib.base_command import Command,ArduinoCommand

def build_circ_ctype(circ_data):
    return {
        'type':enums.CmdType.CIRC_CMD.name,
        'data': {
            'circ_cmd':circ_data
        }
    }

def float_to_byte(fvalue):
    assert(fvalue >= 0.0 and fvalue <= 1.0)
    return int(fvalue*255)

def parse_pattern_conn(args,name):
    line = " ".join(args)

    src_cmds = [
        '{sblk:w} {schip:d} {stile:d} {sslice:d} {sindex:d} port {sport:d}',
        '{sblk:w} {schip:d} {stile:d} {sslice:d} port {sport:d}',
        '{sblk:w} {schip:d} {stile:d} {sslice:d} {sindex:d}',
        '{sblk:w} {schip:d} {stile:d} {sslice:d}'
    ]

    dst_cmds = [
        '{dblk:w} {dchip:d} {dtile:d} {dslice:d} {dindex:d} port {dport:d}',
        '{dblk:w} {dchip:d} {dtile:d} {dslice:d} port {dport:d}',
        '{dblk:w} {dchip:d} {dtile:d} {dslice:d} {dindex:d}',
        '{dblk:w} {dchip:d} {dtile:d} {dslice:d}'
    ]
    result = None
    for dst in dst_cmds:
        for src in src_cmds:
            if result is None:
                cmd = dst + " " + src
                result = parselib.parse(cmd,line)

    if result is None:
        print("usage: %s %s" % (name,cmd))
        return None

    result = dict(result.named.items())
    if not 'sindex' in result:
        result['sindex'] = None
    if not 'dindex' in result:
        result['dindex'] = None
    if not 'sport' in result:
        result['sport'] = None
    if not 'dport' in result:
        result['dport'] = None

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

    result = dict(result.named.items())
    for idx in range(0,n_outs):
        key = 'sign%d' % idx
        if not result[key] in signd:
            print("unknown sign: <%s>" % result[key])
            return None

        result[key] = signd[result[key]]

    return result


class CircLoc:

    def __init__(self,chip,tile,slice,index=None):
        self.chip = chip;
        self.tile = tile;
        self.slice = slice;
        self.index = index;

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
        self.port = port


    def __repr__(self):
        return str(self.loc) + "." + self.port



class AnalogChipCommand(ArduinoCommand):
    CALIBRATE = 0;
    CONFIGURE = 1;
    TEARDOWN = 2;
    def __init__(self):
        ArduinoCommand.__init__(self,cstructs.cmd_t())

    def test_loc(self,block,loc):
        if not loc.chip in range(0,2):
            self.fail("unknown chip <%d>" % loc.chip)
        if not loc.tile in range(0,4):
            self.fail("unknown tile <%d>" % loc.tile)
        if not loc.slice in range(0,4):
            self.fail("unknown slice <%d>" % loc.slice)
        if not loc.index is None and \
           not loc.index in range(0,2):
            self.fail("unknown index <%s>" % loc.index)

        if (block == enums.BlockType.FANOUT.value) \
            or (block == enums.BlockType.TILE.value) \
            or (block == enums.BlockType.MULT.value):
            indices = {
                enums.BlockType.FANOUT: range(0,2),
                enums.BlockType.MULT: range(0,2),
                enums.BlockType.TILE: range(0,4)
            }
            if loc.index is None:
                self.fail("expected index <%s>" % block)

            if not loc.index in indices[block]:
                self.fail("index <%s> must be from indices <%s>" %\
                          (block,indices))

        elif not enums.BlockType(block) is None:
           if not loc.index is None:
               self.fail("expected no index <%s> <%d>" %\
                         (block,loc.index))

        else:
            self.fail("not in block list <%s>" % block)
    def calibrate(self):
        return None

    def disable(self):
        return None

    def configure(self):
        return None

    def execute_command(self,state):
        raise Exception("cannot directly execute analog chip command")

    def apply(self,state):
        ArduinoCommand.execute_command(self,state)


class DisableCmd(AnalogChipCommand):

    def __init__(self,block,chip,tile,slice,index=None):
        AnalogChipCommand.__init__(self)
        self._block = block;
        self._loc = CircLoc(chip,tile,slice,index)
        self.test_loc(self._block,self._loc)

    def disable():
        return self

    @staticmethod
    def name():
        return 'disable'

    @staticmethod
    def desc():
        return "disable a block on the hdacv2 board"


    def build_ctype(self):
        if self._block == enums.BlockType.DAC:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_DAC.name,
                'data':{
                    'circ_loc':self._loc.build_ctype()
                }
            })
        elif self._block == enums.BlockType.MULT:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_MULT.name,
                'data':{
                    'circ_loc':self._loc.build_ctype()
                }
            })
        elif self._block == enums.BlockType.FANOUT:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_FANOUT.name,
                'data':{
                    'circ_loc_idx1':self._loc.build_ctype()
                }
            })
        elif self._block == enums.BlockType.INTEG:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_INTEG.name,
                'data':{
                    'circ_loc':self._loc.build_ctype()
                }
            })
        elif self._block == enums.BlockType.LUT:
            return build_circ_ctype({
                'type':enums.CircCmdType.DISABLE_LUT.name,
                'data':{
                    'circ_loc':self._loc.build_ctype()
                }
            })
        else:
            print("no disable command <%s>" % self._block)
            return None


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

    def __repr__(self):
        return "disable %s.%s" % (self._loc,self._block)

class CalibrateCmd(AnalogChipCommand):

    def __init__(self,chip,tile,slice):
        AnalogChipCommand.__init__(self)
        self._loc = CircLoc(chip,tile,slice)
        self.test_loc(enums.BlockType.NONE,self._loc)

    def calibrate(self):
        return self

    @staticmethod
    def name():
        return 'calib'

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
        line = " ".join(args)
        result = parse_pattern_block(args,0,0,
                                      CalibrateCmd.name(),
                                      index=False)
        return CalibrateCmd(result['chip'],result['tile'],
                            result['slice'])

    def __repr__(self):
        return "calib %s" % self._loc


class UseCommand(AnalogChipCommand):

    def __init__(self,block,loc):
        AnalogChipCommand.__init__(self)
        self.test_loc(block,loc)
        self._loc = loc
        self._block = block

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
        return "use(%s,%s)" % (self._loc,self._block)

class UseDACCmd(UseCommand):


    def __init__(self,chip,tile,slice,value,inv=False):
        UseCommand.__init__(self,
                            enums.BlockType.DAC,
                            CircLoc(chip,tile,slice))

        if value < 0.0 or value > 1.0:
            self.fail("value not in [0,1]: %s" % value)
        if not self._loc.index is None:
            self.fail("dac has no index <%d>" % loc.index)

        self._value = value
        self._inv = inv

    @staticmethod
    def desc():
        return "use a constant dac block on the hdacv2 board"


    @staticmethod
    def parse(args):
        result = parse_pattern_block(args,1,1,
                                     UseDACCmd.name())
        if not result is None:
            return UseDACCmd(
                result['chip'],
                result['tile'],
                result['slice'],
                result['value0'],
                inv=result['sign0']
            )

    def build_ctype(self):
        return build_circ_ctype({
            'type':enums.CircCmdType.USE_DAC.name,
            'data':{
                'dac':{
                    'loc':{
                        'chip':self._loc.chip,
                        'tile':self._loc.tile,
                        'slice':self._loc.slice
                    },
                    'value':float_to_byte(self._value),
                    'inv':self._inv
                }
            }
        })

    @staticmethod
    def name():
        return 'use_dac'

    def __repr__(self):
        st = UseCommand.__repr__(self)
        st + " dac %s inv=%d" % (self._value,self._inv)
        return st



class UseIntegCmd(UseCommand):


    def __init__(self,chip,tile,slice,value,inv=False):
        UseCommand.__init__(self,
                            enums.BlockType.INTEG,
                            CircLoc(chip,tile,slice))
        if value < 0.0 or value > 1.0:
            self.fail("value not in [0,1]: %s" % value)

        if not loc.index is None:
            self.fail("integ has no index <%d>" % loc.index)

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

    def __repr__(self):
        st = UseCommand.__repr__(self)
        st + " integ %s inv=%d" % (self._value,self._inv)
        return st




class UseFanoutCmd(UseCommand):


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


    def __repr__(self):
        st = UseCommand.__repr__(self)
        st + " integ invs=%d" % (self._invs)
        return st



class UseMultCmd(UseCommand):


    def __init__(self,chip,tile,slice,index,
                 coeff=0,use_coeff=False,inv=False):
        UseCommand.__init__(self,
                            enums.BlockType.MULT,
                            CircLoc(chip,tile,slice,index))

        if value < 0.0 or value > 1.0:
            self.fail("value not in [0,1]: %s" % value)

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

    def __repr__(self):
        st = UseCommand.__repr__(self)
        st += " mult %s inv=%s" % (self._value,self._inv)
        return st


class ConnectionCmd(AnalogChipCommand):

    def __init__(self,src_blk,src_loc,
                 dst_blk,dst_loc,
                 make_conn=True):
        AnalogChipCommand.__init__(self)
        assert(isinstance(src_loc,CircPortLoc))
        self._src_blk = src_blk;
        self._src_loc = src_loc;
        self.test_loc(self._src_blk, self._src_loc.loc)
        assert(isinstance(dst_loc,CircPortLoc))
        self._dst_blk = dst_blk;
        self._dst_loc = dst_loc;
        self.test_loc(self._dst_blk, self._dst_loc.loc)

    def __repr__(self):
        return "conn %s.%s <-> %s.%s" % (self._src_blk,self._src_loc,
                                         self._dst_blk,self_dst_loc)
class BreakConnCmd(ConnectionCmd):

    def __init__(self,src_blk,src_loc,
                 dst_blk,dst_loc):
        ConnectionCmd.__init__(src_blk,src_loc,
                               dst_blk,dst_loc,True)

    def disable(self):
        return self

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
            srcloc = CircPortLoc(result['schip'],result['stile'],
                                 result['sslice'],result['sport'],
                                 result['sindex'])
            dstloc = CircPortLoc(result['dchip'],result['dtile'],
                                 result['dslice'],result['dport'],
                                 result['dindex'])


            return ConnectionCmd(
                result['sblk'],srcloc,
                result['dblk'],dstloc,
                make_conn=False)



    def __repr__(self):
        return "break %s" % (ConnectionCmd.__repr__(self))

class MakeConnCmd(ConnectionCmd):

    def __init__(self,src_blk,src_loc,
                 dst_blk,dst_loc):
        ConnectionCmd.__init__(src_blk,src_loc,
                               dst_blk,dst_loc,True)

    def configure(self):
        return self

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
            srcloc = CircPortLoc(result['schip'],result['stile'],
                                 result['sslice'],result['sport'],
                                 result['sindex'])
            dstloc = CircPortLoc(result['dchip'],result['dtile'],
                                 result['dslice'],result['dport'],
                                 result['dindex'])


            return ConnectionCmd(
                result['sblk'],srcloc,
                result['dblk'],dstloc,
                make_conn=True)


    def break_conn(self):
        return BreakConnectionCmd(self._src_blk,self._src_loc,
                             self._dst_blk,self._dst_loc)


    def __repr__(self):
        return "make %s" % (ConnectionCmd.__repr__(self))
