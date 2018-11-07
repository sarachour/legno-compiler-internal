import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
from lib.exp_command import *
from lib.circ_command import *

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
    UseFanoutCmd,
    MakeConnCmd,
    DisableCmd,
    MakeConnCmd,
    BreakConnCmd,
    CalibrateCmd,
    # experiment commands
    ResetCmd,
    RunCmd,
    UseOscilloscopeCmd,
    UseDueDACCmd,
    UseDueADCCmd,
    UseAnalogChipCmd,
    SetNumADCSamplesCmd,
    SetDueDACValuesCmd,
    GetOscValuesCmd,
    GetDueADCValuesCmd
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

