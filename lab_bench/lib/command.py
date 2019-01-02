import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
from lib.exp_command import *
from lib.chip_command import *
from lib.virt_command import *

'''
###################
CIRCUIT COMMANDS
###################
'''

COMMANDS = [
    # dac/adc commands
    UseDACCmd,
    UseIntegCmd,
    UseMultCmd,
    GetIntegStatusCmd,
    UseFanoutCmd,
    MakeConnCmd,
    #DisableCmd,
    MakeConnCmd,
    #BreakConnCmd,
    #CalibrateCmd,
    # experiment commands dispatched to microcontroller
    MicroResetCmd,
    MicroRunCmd,
    MicroTeardownChipCmd,
    MicroSetupChipCmd,
    MicroGetOverflowCmd,
    MicroUseOscCmd,
    MicroUseDACCmd,
    MicroUseADCCmd,
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
    # virtual commands
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

