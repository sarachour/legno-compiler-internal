import argparse
import os
import sys
import shutil
import moira.model as modellib
import moira.drive as driver
import moira.time_fit as time_fit
import moira.signal_fit as signal_fit
import moira.fft_gen as fft_gen
import moira.noise_fit as noise_fit
import moira.build_bbmodel as build_bbmodel
import moira.inpgen as inpgen
import traceback

sys.path.insert(0,os.path.abspath("lab_bench"))

import lab_bench.lib.state as lab_state


def notify(email,text):
    with open('report.txt','w') as fh:
        fh.write(text)

    cmd = 'mail -s "Moira process exited" %s < report.txt' % \
          email
    os.system(cmd)

def loop(state,model):
    print(model.db)
    inpgen.execute(model)
    print(model.db)
    driver.execute(state,model)
    time_fit.execute(model)
    signal_fit.execute(model)
    fft_gen.execute(model)
    noise_fit.execute(model)
    build_bbmodel.execute(model)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, help="ip address of oscilloscope.")
    parser.add_argument("--email", type=str, help="email address to send notifications for.")
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

    try:

        mgr = modellib.build_manager()
        if args.subparser_name == "due_dac":
            model = mgr.get('due_dac%d' % args.dac_id)
            loop(state,model)

        elif args.subparser_name == "vdiv":
            model = mgr.get('vdiv%d' % args.dac_id)
            loop(state,model)

        else:
            raise Exception("unhandled: %s" % \
                            rgs.subparser_name)

    except Exception as e:
        msg = "=== Exception ===\n%s\n\n" % e
        msg += "=== Trace ===\n%s\n\n" % \
               traceback.format_exc()
        msg += "=== Details ===\n%s\n\n" % \
               sys.exc_info()[0]

        print(msg)
        if not args.email is None:
            notify(args.email,msg)
            sys.exit(1)

    msg = "<<< SUCCESS >>>"
    if not args.email is None:
        notify(args.email,msg)
        sys.exit(0)

main()

