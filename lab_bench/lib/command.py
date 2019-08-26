import parse as parselib
import lab_bench.lib.cstructs as cstructs
import lab_bench.lib.enums as enums
from lab_bench.lib.chipcmd.use import *
from lab_bench.lib.chipcmd.conn import *
from lab_bench.lib.chipcmd.calib import *
from lab_bench.lib.chipcmd.profile import *
from lab_bench.lib.chipcmd.misc import *
from lab_bench.lib.expcmd.micro_action import *
from lab_bench.lib.expcmd.micro_getter import *
from lab_bench.lib.expcmd.osc import *
from lab_bench.lib.expcmd.client import *
'''
###################
CIRCUIT COMMANDS
###################
'''

COMMANDS = [
    # dac/adc commands
    UseDACCmd,
    UseADCCmd,
    UseLUTCmd,
    WriteLUTCmd,
    UseIntegCmd,
    UseMultCmd,
    GetIntegStatusCmd,
    GetADCStatusCmd,
    UseFanoutCmd,
    MakeConnCmd,
    # circuit commands that are automatically generated
    DisableCmd,
    BreakConnCmd,
    CalibrateCmd,
    # offset commands
    GetStateCmd,
    ProfileCmd,
    # experiment commands dispatched to microcontroller
    MicroResetCmd,
    MicroRunCmd,
    MicroGetStatusCmd,
    MicroUseOscCmd,
    MicroUseArdDACCmd,
    MicroUseArdADCCmd,
    MicroUseAnalogChipCmd,
    MicroSetSimTimeCmd,
    MicroSetDACValuesCmd,
    MicroGetADCValuesCmd,
    MicroComputeOffsetsCmd,
    MicroGetNumADCSamplesCmd,
    MicroGetNumDACSamplesCmd,
    MicroGetTimeDeltaCmd,
    # oscilloscope-only commands
    OscGetValuesCmd,
    OscSetVoltageRangeCmd,
    OscSetupTrigger,
    OscSetSimTimeCmd,
    # virtual commands, deprecated
    WaitForKeypress
]


def parse(line):
    if line.startswith("#"):
        return None

    args = line.strip().split()
    if len(args) == 0:
        return None
    for cmd in COMMANDS:
        if args[0] == cmd.name():
            obj = cmd.parse(args)
            return obj

    if args[0] == 'help':
        for cmd in COMMANDS:
            print("%s: %s" % (cmd.name(),cmd.desc()))

    return None


def profile(state,obj, \
            recompute=False, \
            clear=False, \
            bootstrap=False, \
            n=5):
    if isinstance(obj,UseCommand):
        dbkey = obj.to_key(calib_mode=state.calib_mode)
        result = state.state_db.get(dbkey)
        print(">> set state")
        backup_cached = obj.cached
        obj.cached = True
        obj.execute(state)
        print(">> profile")
        ProfileCmd(obj.block_type,
                   obj.loc.chip,
                   obj.loc.tile,
                   obj.loc.slice,
                   index=obj.loc.index,
                   clear=clear,
                   bootstrap=bootstrap,
                   n=n) \
                   .execute(state)
        obj.cached = backup_cached



def calibrate(state,obj,recompute=False, \
              calib_mode=CalibType.MIN_ERROR):
    if isinstance(obj,UseCommand):
        dbkey = obj.to_key(calib_mode)
        if not (state.state_db.has(dbkey)) or \
           recompute:
            obj.cached = False
            obj.execute(state)
            print(">> resetting defaults")
            DefaultsCommand().execute(state)
            print(">> set state")
            obj.execute(state)
            print(">> calibrate [%f]" % obj.max_error)
            CalibrateCmd(obj.block_type,
                         obj.loc.chip,
                         obj.loc.tile,
                         obj.loc.slice,
                         obj.loc.index,
                         calib_mode=calib_mode) \
                         .execute(state)


        result = state.state_db.get(dbkey)
