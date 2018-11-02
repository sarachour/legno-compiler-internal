import sys
import datetime
from devices.arduino_due import ArduinoDue
from devices.sigilent_osc import Sigilent1020XEOscilloscope
import argparse
import time
import struct
import json

parser = argparse.ArgumentParser()
parser.add_argument("--native", action='store_true',help="use native mode for arduino DUE.")
parser.add_argument("--ip", type=str, help="ip address of oscilloscope.")
parser.add_argument("--port", type=int, default=5024, help="port number of oscilloscope.")
parser.add_argument("--output", type=str, default="noise_output", help="output directory for data files.")

args = parser.parse_args()
ard = ArduinoDue(native=args.native)
osc = Sigilent1020XEOscilloscope(args.ip,args.port)
assert(ard.open())

def menu():
    st = ""
    st += "start the experiment."
    st += "  start\n\n"
    st += "add a dc component into the signal.\n"
    st += "  sig dac# dc <ampl>\n\n"
    st += "add a sin component into the signal.\n"
    st += "  sig dac# sin <ampl> <phase> <offset>\n\n"
    st += "set the circuit configuration.\n"
    st += "  circ <circ#>\n\n"
    st += "set an argument\n"
    st += "  arg <arg_name> <arg_value>\n\n"
    st += "compile the experiment\n"
    st += "  compile\n\n"
    st += "clear the experiment\n"
    st += "  clear\n\n"
    st += "quit the program.\n"
    st += "  quit\n\n"
    st += "read the experiment specification\n"
    st += "  read\n\n"
    return st

def clear_experiment():
    ard.write(chr(4))

def compile_experiment():
    ard.write(chr(7))

def start_experiment():
    osc.setup();
    props = osc.get_properties()
    print("=== oscillator params ===")
    for key,val in props.items():
        print("%s : %s" % (key,val))

    input("<press enter to start>")
    ard.write(chr(3))
    osc.acquire()
    print("waiting..")
    line = ard.readline()
    while "::done::" not in line:
        print(line)
        line = ard.readline()

    print("<done>")
    data = {}
    for channel_no in props['channels']:
        t,v = osc.waveform(channel_no,
                           voltage_scale=props['voltage_scale'][channel_no],
                           time_scale=props['time_scale'],
                           voltage_offset=props['voltage_offset'][channel_no])

        data[channel_no] = {'time':t,'voltage':v}


    with open('output.json','w') as fh:
        fh.write(json.dumps(data))



def read_experiment():
    ard.write(chr(6))

def quit_experiment():
    ard.write(chr(5))

def set_circuit(circ_num):
    print("TODO: set circuit")

def set_argument(argname,argval):
    print("TODO: set argument")

def add_sin_wave(dacid,ampl,freq,phase):
    ard.write(chr(0))
    ard.write(chr(dacid))
    ard.write(chr(1))
    ba = float_to_bytes(float(ampl))
    ard.write_bytes(ba)
    ba = float_to_bytes(float(freq))
    ard.write_bytes(ba)
    ba = float_to_bytes(float(phase))
    ard.write_bytes(ba)


def float_to_bytes(value):
    ba = bytearray(struct.pack('<f',value))
    return ba

def add_const(dacid,ampl):
    ard.write(chr(0))
    ard.write(chr(dacid))
    ard.write(chr(0))
    ba = float_to_bytes(float(ampl))
    ard.write_bytes(ba)

def exec_cmd(cmd,args):
    def assert_len(lst,length):
        if len(lst) == length:
            return True
        else:
            print("expected %d args: <%s>" % (length,lst))
            return False

    if cmd == "start":
        if not assert_len(args,0):
            return
        start_experiment()

    elif cmd == "clear":
        if not assert_len(args,0):
            return
        clear_experiment()

    elif cmd == "quit":
        if not assert_len(args,0):
            return
        quit_experiment()

    elif cmd == "compile":
        if not assert_len(args,0):
            return;
        compile_experiment()

    elif cmd == "read":
        if not assert_len(args,0):
            return
        read_experiment()

    elif cmd == "circ":
        if not assert_len(args,1):
            return
        set_circuit(int(args[0]))

    elif cmd == "arg":
        if not assert_len(args,2):
            return
        set_argument(args[0], float(args[1]))

    elif cmd == "sig":
        if len(args) < 2:
            print("expected at least 2 args: <%d>" % args)
            return

        dacnum = int(args[0])
        if not (dacnum == 0 or dacnum == 1):
            print("unknown dac <%d>" % dacnum)
            return

        subcmd = args[1]
        subargs = args[2:]
        if subcmd == "dc":
            if not assert_len(subargs, 1):
                return

            add_const(dacnum,float(subargs[0]))

        elif subcmd == "sin":
            if not assert_len(subargs, 3):
                return

            add_sin_wave(dacnum,float(subargs[0]),float(subargs[1]),float(subargs[2]))

        else:
            print("unknown signal component <%s>" % subcmd)
            return

    elif cmd == "help":
        print(menu())

    else:
       print("unknown command <%s> %s" % (cmd,args))
       return

try:
    while(True):
        time.sleep(1)
        line = ard.try_readline()
        while not line is None:
            print(line)
            line = ard.try_readline()

        line = input("due>> ")
        args = line.strip().split()
        exec_cmd(args[0],args[1:])

except Exception as e:
    print("<< closing devices >>")
    osc.close()
    ard.close()
    raise e


