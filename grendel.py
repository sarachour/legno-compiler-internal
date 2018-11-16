import argparse
import os
import sys

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

def test_dac_on_input(dac_id,input_fn,num_trials=5):
    prog = []
    def q(stmt):
        prog.append(stmt)

    boilerplate_osc(prog,20.0,"inp0+1.5",[dac_id])
    q('set_due_dac_values %d %s' % (dac_id,input_fn))
    q('run')
    for trial in range(0,num_trials):
        q('get_osc_values direct data%d.json' % trial)

    q('reset')
    return prog

def exec_prog(state,blockid,index,prog):
    outdir = "outputs/grendel/%s/%s/" % (blockid,index)


    if not os.path.exists(outdir):
        os.makedirs(outdir)

    scriptfile = "%s/prog.grendel" % outdir
    with open(scriptfile,'w') as fh:
        fh.write("\n".join(prog))

    lab_handler.main_script(state,scriptfile)

    for dirname, subdirlist, filelist in os.walk(outdir):
        for fname in filelist:
            if fname.endswith('json'):
                print(fname)



def due_dac_runner(state,dac_id):
    inputs = [
        "0", "1",
        "1.0*math.sin(1.0*t)",
        "1.0*math.sin(10.0*t)",
        "1.0*math.sin(100.0*t)",
        "0.2*math.sin(1.0*t)"
    ]
    for index,input_sig in enumerate(inputs):
        exec_prog(state,"dac[0]",index,test_dac_on_input(dac_id,input_sig))



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
                  ard_native=args.native,
                  validate=True)


    if args.subparser_name == "due_dac":
        due_dac_runner(state,args.dac_id)
    else:
        raise Exception("unhandled: %s" % args.subparser_name)


main()

