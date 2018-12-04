import argparse
import os
import sys
import shutil
import moira.model as modellib
import moira.drive as driver
import moira.align as align
import moira.fit as modelfit
import moira.inpgen as inpgen

sys.path.insert(0,os.path.abspath("lab_bench"))

import lab_bench.lib.state as lab_state


def loop(state,model,sim_time):
    print(model.db)
    #inpgen.execute(model)
    driver.execute(state,model,sim_time)
    align.execute(model)
    modelfit.execute(model)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, help="ip address of oscilloscope.")
    parser.add_argument("--port", type=int, default=5024, help="port number of oscilloscope.")
    parser.add_argument("--sim-time", type=float, default=10.0, help="time in milliseconds to simulate.")
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


    mgr = modellib.build_manager()
    if args.subparser_name == "due_dac":
        model = mgr.get('due_dac%d' % args.dac_id)
        loop(state,model,args.sim_time)

    elif args.subparser_name == "vdiv":
        model = mgr.get('vdiv%d' % args.dac_id)
        loop(state,model,args.sim_time)

    else:
        raise Exception("unhandled: %s" % args.subparser_name)


main()

