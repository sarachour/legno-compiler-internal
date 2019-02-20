import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
from lib.chipcmd.use import *
from lib.chipcmd.config import *
from lib.chipcmd.conn import *
from lib.chipcmd.calib import *
from lib.chipcmd.misc import *
from lib.expcmd.micro_action import *
from lib.expcmd.micro_getter import *
from lib.expcmd.osc import *
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
    #DisableCmd,
    #BreakConnCmd,
    #CalibrateCmd,
    # experiment commands dispatched to microcontroller
    MicroResetCmd,
    MicroRunCmd,
    MicroTeardownChipCmd,
    MicroSetupChipCmd,
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
    OscSetSimTimeCmd
    # virtual commands, deprecated
    #SetReferenceFunction
]


def parse(line):
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

