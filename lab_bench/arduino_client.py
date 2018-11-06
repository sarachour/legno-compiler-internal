import lib.command as cmd
import sys
import argparse
from devices.arduino_due import ArduinoDue
from devices.sigilent_osc import Sigilent1020XEOscilloscope

from lib.command import ArduinoCommand
import time

class State:

    def __init__(self,osc_ip,osc_port,ard_native,validate=False):
        self.arduino = ArduinoDue(native=ard_native)
        self.oscilloscope = Sigilent1020XEOscilloscope(
            osc_ip, osc_port)
        self.prog = [];
        self.use_osc = False;
        self.use_adc = False;
        self.use_analog_chip = False;
        self.n_samples = 0
        self.TIME_BETWEEN_SAMPLES = 3.0*1e-6
        self.dummy = validate

    def close(self):
        self.arduino.close()
        self.oscilloscope.close()

    def initialize(self):
        if self.dummy:
            return

        print("-> setup oscilloscope")
        self.oscilloscope.setup()
        print("-> setup arduino")
        self.arduino.open()

    def enqueue(self,stmt):
        if stmt.test():
            self.prog.append(stmt)
        else:
            print("[error] " + stmt.error_msg())

    def calibrate_chip(self):
        if not self.use_analog_chip:
            return

        for stmt in self.prog:
            if isinstance(stmt, cmd.AnalogChipCommand):
                calib_stmt = stmt.calibrate()
                if not calib_stmt is None:
                    yield calib_stmt

    def teardown_chip(self):
        if not self.use_analog_chip:
            return

        for stmt in self.prog:
            if isinstance(stmt, cmd.AnalogChipCommand):
                dis_stmt = stmt.disable()
                if not dis_stmt is None:
                    yield dis_stmt

    def configure_chip(self):
        if not self.use_analog_chip:
            return

        for stmt in self.prog:
            if isinstance(stmt, cmd.AnalogChipCommand):
                config_stmt = stmt.configure()
                if not config_stmt is None:
                    yield config_stmt




def execute(state,line):
    if line.startswith("#"):
        print(line)
        print("<comment, skipping..>")
        return

    command_obj = cmd.parse(line)
    if command_obj is None:
        print("<unknown command: %s>" % line)
        return False

    if not command_obj.test():
        print("[error] %s" % command_obj.error_msg())
        return False

    if isinstance(command_obj, cmd.AnalogChipCommand):
        state.enqueue(command_obj)
        return True

    elif isinstance(command_obj,cmd.Command):
        command_obj.execute(state)
        return True

    else:
        print("unhandled..")
        print(command_obj)
        return False

def main_stdout(state):
    while True:
        line = input("ardc>> ")
        if line == "quit":
            sys.exit(0)

        execute(state,line)


def main_script(state,filename):
    with open(filename,'r') as fh:
        for idx,line in enumerate(fh):
            print("loc: %d" % idx)
            if not (execute(state,line.strip())):
                sys.exit(1)


parser = argparse.ArgumentParser()
parser.add_argument("--native", action='store_true',help="use native mode for arduino DUE.")
parser.add_argument("--ip", type=str, help="ip address of oscilloscope.")
parser.add_argument("--port", type=int, default=5024, help="port number of oscilloscope.")
parser.add_argument("--output", type=str, default="noise_output", help="output directory for data files.")
parser.add_argument("--script", type=str, help="read data using script.")
parser.add_argument("--validate", action='store_true', help="validate script")



args = parser.parse_args()


state = State(args.ip,args.port,
              ard_native=args.native,
              validate=args.validate)

state.initialize()
if not args.validate and (args.ip is None):
    raise Exception("must include ip address of oscilloscope")

try:
    if args.script == None:
        main_stdout(state)
    else:
        main_script(state,args.script)

except Exception as e:
    print("<< closing devices >>")
    state.close()
    raise e

