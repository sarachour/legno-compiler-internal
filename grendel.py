import argparse
import os
import sys
import shutil

sys.path.insert(0,os.path.abspath("lab_bench"))

import lab_bench.lib.state as lab_state
import lab_bench.lib.command_handler as lab_handler

def boilerplate_osc(prog,sim_time,ref_fun,dacs):
    def q(stmt):
        prog.append(stmt)


    q('set_ref_func %s' % ref_fun)
    q('set_sim_time %f' % sim_time)
    q('get_num_samples')
    q('get_time_between_samples')
    q('use_osc')
    for dac in dacs:
        q('use_due_dac %d' % dac)

    q('compute_offsets')

def test_vdiv_on_input(dac_id,input_fn,num_trials=1):
    prog = []
    outfiles = []
    def q(stmt):
        prog.append(stmt)

    boilerplate_osc(prog,10.0,"inp0+1.625",[dac_id])
    q('set_due_dac_values %d %s' % (dac_id,input_fn))
    q('run')
    for trial in range(0,num_trials):
        q('get_osc_values differential data%d.json' % trial)
        q('run')
        outfiles.append("data%d" % trial)

    q('reset')
    return outfiles,prog


def test_dac_on_input(dac_id,input_fn,num_trials=1):
    prog = []
    outfiles = []
    def q(stmt):
        prog.append(stmt)

    boilerplate_osc(prog,10.0,"inp0+1.625",[dac_id])
    q('set_due_dac_values %d %s' % (dac_id,input_fn))
    q('run')
    for trial in range(0,num_trials):
        q('get_osc_values direct data%d.json' % trial)
        q('run')
        outfiles.append("data%d" % trial)

    q('reset')
    return outfiles,prog

def exec_prog(state,blockid,index,prog,outfiles):
    outdir = "outputs/grendel/%s/%s" % (blockid,index)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    scriptfile = "%s/prog.grendel" % outdir
    with open(scriptfile,'w') as fh:
        srccode = "\n".join(prog)
        print(srccode)
        fh.write(srccode)

    input("<run experiment>")
    lab_handler.main_script(state,scriptfile)

    for outfile in outfiles:
        json_file = "%s.json" % outfile
        png_file = "%s.png" % outfile
        if os.path.isfile(json_file):
            shutil.move(json_file, "%s/%s" % (outdir,json_file))
        if os.path.isfile(png_file):
            shutil.move(png_file, "%s/%s" % (outdir,png_file))

        print("-> moving %s" % outfile)

def vdiv_runner(state,dac_id):
    inputs = [
        "0", "1", "-1",
        "1.0*math.sin(1.0*t)",
        "1.0*math.sin(10.0*t)",
        "1.0*math.sin(100.0*t)",
        "0.2*math.sin(1.0*t)"
    ]
    for index,input_sig in enumerate(inputs):
        outfiles,prog = test_vdiv_on_input(dac_id,input_sig)
        exec_prog(state,"vdiv[0]",index,prog,outfiles)


def due_dac_runner(state,dac_id):
    inputs = [
        "0", "1", "-1",
        "1.0*math.sin(1.0*t)",
        "1.0*math.sin(10.0*t)",
        "1.0*math.sin(100.0*t)",
        "0.2*math.sin(1.0*t)"
    ]
    for index,input_sig in enumerate(inputs):
        outfiles,prog = test_dac_on_input(dac_id,input_sig)
        exec_prog(state,"dac[0]",index,prog,outfiles)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, help="ip address of oscilloscope.")
    parser.add_argument("--port", type=int, default=5024, help="port number of oscilloscope.")
    parser.add_argument("--native", action='store_true',help="use native mode for arduino DUE.")

    subparsers = parser.add_subparsers(dest='subparser_name',
                                       help='blocks to exercise.')

    due_dac = subparsers.add_parser('due_dac', help='profile the Arduino Due DAC')
    due_dac.add_argument('--dac-id', type=int,default=0, help='dac id to evaluate.')

    volt_div = subparsers.add_parser('vdiv', help='generate the voltage divider')
    volt_div.add_argument('--dac-id', type=int,default=0, help='dac id to evaluate.')


    hdac_v2= subparsers.add_parser('analog_chip', help='exercise a block in the chip.')
    hdac_v2.add_argument("--block",type=str,help="block to exercise")
    hdac_v2.add_argument("--chip", type=int,help="chip number.")
    hdac_v2.add_argument("--tile", type=int,help="tile number.")
    hdac_v2.add_argument("--slice", type=int,help="slice number.")
    hdac_v2.add_argument("--index", type=int,help="index number.")

    args = parser.parse_args()

    state = lab_state.State(args.ip,args.port,
                  ard_native=args.native)

    state.initialize()

    dac_setup_message = """
    DAC Experiment Setup Instructions:
    1. Make sure you set voltage threshhold for the clock to 100mV
    2. Clip the EXT signal probe to the SDA port and the ground probe to Arduino GND
    3. Clip the CH1 signal probe to DAC0/1 and the ground probe to Arduino ground
    """

    vdiv_setup_message = """
    VDiv circuit Setup Instructions:
    0. When the chip is off, connect breadboard voltage to 3.3V voltage source from Arduino Due, and the ground lead to the GND pin in the Arduino Due.
    1. Make sure you set voltage threshhold for the clock to 100mV
    2. Clip the EXT signal probe to the SDA port and the ground probe to Arduino GND
    3. Clip the CH1 signal probe to the purple wire on the breadboard and the ground probe to breadboard  GND. (left pair for VDIV0, right pair for VDIV1)
    4. Clip the CH2 signal probe to the gray wire on the breadboard and the ground probe to breadboard  GND.
    """
    if args.subparser_name == "due_dac":
        print(dac_setup_message)
        input("<i'm ready!>")
        due_dac_runner(state,args.dac_id)
    elif args.subparser_name == "vdiv":
        print(vdiv_setup_message)
        input("<i'm ready!>")
        vdiv_runner(state,args.dac_id)

    else:
        raise Exception("unhandled: %s" % args.subparser_name)


main()

