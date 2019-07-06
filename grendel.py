import argparse
import sys
import os
import util.config as CONFIG
#sys.path.insert(0,os.path.abspath("."))

from lab_bench.lib.command_handler import main_stdout,  \
    main_script, \
    main_script_calibrate, \
    main_script_profile, \
    main_dump_db
from lab_bench.lib.base_command import ArduinoCommand
from lab_bench.lib.env import GrendelEnv


parser = argparse.ArgumentParser()
parser.add_argument("--native", action='store_true', \
                    help="use native mode for arduino DUE.")
parser.add_argument("--no-oscilloscope", action='store_true', \
                    help="use native mode for arduino DUE.")
parser.add_argument("--ip", type=str, help="ip address of oscilloscope.")
parser.add_argument("--port", type=int, default=5024, \
                    help="port number of oscilloscope.")
parser.add_argument("--output", type=str, default="noise_output", \
                    help="output directory for data files.")
parser.add_argument("script", type=str, \
                    help="read data using script.")
parser.add_argument("--validate", action='store_true', \
                    help="validate script")
parser.add_argument("--debug", action='store_true', \
                    help="debug script")
parser.add_argument("--calibrate", action='store_true', \
                    help="calibrate uncalibrated components")
parser.add_argument("--targeted", action='store_true', \
                    help="targeted calibration of uncalibrated components")

parser.add_argument("--infer", action='store_true', \
                    help="infer uncalibrated components")
parser.add_argument("--profile", action='store_true', \
                    help="profile components on chip")
parser.add_argument("--clear-profile", action='store_true', \
                    help="clear profiles on chip")
parser.add_argument("--recompute", action='store_true', \
                    help="recompute calibration codes")
parser.add_argument("--dump-db", action='store_true', \
                    help="dump the database contents to files")
parser.add_argument("--dry-run", action='store_true', \
                    help="dump the database contents to files")



args = parser.parse_args()

if args.dump_db:
    state = GrendelEnv(None,None,
                       ard_native=args.native,
                       validate=args.validate)

    main_dump_db(state)
    sys.exit(0)

if args.debug:
    ArduinoCommand.set_debug(True)
else:
    ArduinoCommand.set_debug(False)

ip = args.ip
if args.ip is None and not args.no_oscilloscope:
    ip = CONFIG.OSC_IP
elif args.no_oscilloscope:
    ip = None

state = GrendelEnv(ip,args.port,
              ard_native=args.native,
              validate=args.validate)

state.initialize()

if args.calibrate:
    assert(args.script != None)
    succ = main_script_calibrate(state,args.script, \
                                 recompute=args.recompute,
                                 targeted=args.targeted)
    if not succ:
        print("[ERROR] some calibration steps failed..")
        sys.exit(1)

    if args.infer:
        print("<< inferring models for compiler >>")
        retcode = os.system("python3 infer_models.py")

elif args.profile:
    succ = main_script_profile(state,args.script, \
                               recompute=args.recompute,
                               clear=args.clear_profile)
if args.dry_run:
    sys.exit(0)

try:
    if args.script == None:
        main_stdout(state)
    else:
        main_script(state,args.script)

except Exception as e:
    print("<< closing devices >>")
    state.close()
    raise e

