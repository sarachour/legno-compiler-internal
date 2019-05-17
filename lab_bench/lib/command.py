import parse as parselib
import lab_bench.lib.cstructs as cstructs
import lab_bench.lib.enums as enums
from lab_bench.lib.chipcmd.use import *
from lab_bench.lib.chipcmd.config import *
from lab_bench.lib.chipcmd.conn import *
from lab_bench.lib.chipcmd.calib import *
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
    ConfigDACCmd,
    UseDACCmd,
    UseADCCmd,
    UseLUTCmd,
    WriteLUTCmd,
    UseIntegCmd,
    ConfigIntegCmd,
    UseMultCmd,
    ConfigMultCmd,
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
    CharacterizeCmd,
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

def profile(state,obj):
    if isinstance(obj,UseCommand):
        dbkey = obj.to_key()
        if (state.state_db.has(dbkey)):
            data = state.state_db.get(dbkey)
            print(obj)
            print(data.state)
            data.write_dataset(state.state_db)

def calibrate(state,obj,recompute=False):
    if isinstance(obj,UseCommand):
        dbkey = obj.to_key()
        if not (state.state_db.has(dbkey)) or \
           not state.state_db.get(dbkey).success or \
           recompute:
            obj.cached = False
            obj.execute(state)
            print(">> resetting defaults")
            DefaultsCommand().execute(state)
            print(">> set state")
            obj.execute(state)
            print(">> calibrate [%f]" % obj.max_error)
            succ = CalibrateCmd(obj.block_type,
                                obj.loc.chip,
                                obj.loc.tile,
                                obj.loc.slice,
                                obj.loc.index,
                                max_error=obj.max_error).execute(state)
            if succ:
                print(">> characterize")
                CharacterizeCmd(obj.block_type,
                            obj.loc.chip,
                            obj.loc.tile,
                            obj.loc.slice,
                            obj.loc.index).execute(state)

            else:
                print("CALIBRATE FAILED")

        result = state.state_db.get(dbkey)
        if result.success:
            print("[[SUCCESS!]]")
            return True
        else:
            print("[[FAILURE]]")
            return False
    return None
