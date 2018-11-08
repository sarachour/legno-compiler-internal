import lib.command as cmd
import sys
import argparse
from devices.arduino_due import ArduinoDue
from devices.sigilent_osc import Sigilent1020XEOscilloscope 
import devices.sigilent_osc as osclib

from lib.base_command import FlushCommand, ArduinoCommand
import time

class State:

    def __init__(self,osc_ip,osc_port,ard_native,validate=False):
        if not validate:
            self.arduino = ArduinoDue(native=ard_native)
            self.oscilloscope = Sigilent1020XEOscilloscope(
                osc_ip, osc_port)
        self.prog = [];

        ## State committed to chip
        self.use_osc = False;

        self._use_adc = {};
        self._use_dac = {}
        self.use_analog_chip = None;
        self.n_samples = None;
        self.reset();

        self.TIME_BETWEEN_SAMPLES = 3.0*1e-6
        self.dummy = validate

    def reset(self):
        self.use_analog_chip = False;
        self.n_samples = 0

        for adc_id in range(0,4):
            self._use_adc[adc_id] = False

        self._use_dac = {}
        for dac_id in range(0,2):
            self._use_dac[dac_id] = False

    def use_dac(self,dac_id):
        self._use_dac[dac_id] = True

    def use_adc(self,adc_id):
        self._use_adc[adc_id] = True

    def adcs_in_use(self):
        for adc_id,in_use in self._use_adc.items():
            if in_use:
                yield adc_id

    def dacs_in_use(self):
        for dac_id,in_use in self._use_dac.items():
            if in_use:
                yield dac_id



    def close(self):
        if not self.dummy:
            self.arduino.close()
            self.oscilloscope.close()

    def initialize(self):
        if self.dummy:
            return

        print("-> setup oscilloscope")
        self.oscilloscope.setup()
        print("-> setup arduino")
        self.arduino.open()
        flush_cmd = FlushCommand()
        while not flush_cmd.execute(self):
            continue

    def enqueue(self,stmt):
        if stmt.test():
            print("[enq] %s" % stmt)
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
                print("[config] %s" % stmt)
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
        print("<unknown command: (%s)>" % line)
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
        elif line.strip() == "":
            continue

        execute(state,line)


def main_script(state,filename):
    with open(filename,'r') as fh:
        for idx,line in enumerate(fh):
            print("ardc>> %s" % line.strip())
            if line == "quit":
                sys.exit(0)
            elif line.strip() == "":
                continue
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

if not args.validate and (args.ip is None):
    raise Exception("must include ip address of oscilloscope")

state.initialize()
hist_mode = state.oscilloscope.get_history_mode()
print("history mode: %s" % hist_mode)
trig_mode = state.oscilloscope.get_trigger_mode()
print("trigger mode: %s" % trig_mode)
trig_setting = state.oscilloscope.get_trigger()
print("trigger setting: %s" % trig_setting)
input("configure trigger?")
new_trigger = osclib.Trigger(osclib.TriggerType.EDGE,
                      state.oscilloscope.ext_channel(),
                      osclib.HRTime(4.24e-10),
                      min_voltage=0.068,
                      which_edge=osclib.TriggerSlopeType.ALTERNATING_EDGES
)
state.oscilloscope.auto()
state.oscilloscope.set_trigger(new_trigger)
state.oscilloscope.set_trigger_mode(osclib.TriggerModeType.NORM)
state.oscilloscope.set_history_mode(True)
print()
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

