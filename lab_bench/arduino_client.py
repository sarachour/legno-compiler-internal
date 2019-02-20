import argparse
import sys
import os
sys.path.insert(0,os.path.abspath("."))

from lab_bench.lib.command_handler import main_stdout, main_script
from lab_bench.lib.base_command import ArduinoCommand
from lab_bench.lib.state import State


parser = argparse.ArgumentParser()
parser.add_argument("--native", action='store_true',help="use native mode for arduino DUE.")
parser.add_argument("--ip", type=str, help="ip address of oscilloscope.")
parser.add_argument("--port", type=int, default=5024, help="port number of oscilloscope.")
parser.add_argument("--output", type=str, default="noise_output", help="output directory for data files.")
parser.add_argument("--script", type=str, help="read data using script.")
parser.add_argument("--validate", action='store_true', help="validate script")
parser.add_argument("--debug", action='store_true', help="debug script")



args = parser.parse_args()

if args.debug:
    ArduinoCommand.set_debug(True)
else:
    ArduinoCommand.set_debug(False)

state = State(args.ip,args.port,
              ard_native=args.native,
              validate=args.validate)

state.initialize()

try:
    if args.script == None:
        main_stdout(state)
    else:
        main_script(state,args.script)

except Exception as e:
    print("<< closing devices >>")
    state.close()
    raise e

