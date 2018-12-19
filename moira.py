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
    prog = True
    inpgen.execute(model)
    while prog:
        prog = False
        print(model.db)
        prog = prog or driver.execute(state,model)
        prog = prog or time_fit.execute(model)
        prog = prog or signal_fit.execute(model)
        prog = prog or fft_gen.execute(model)
        prog = prog or noise_fit.execute(model)
        prog = prog or build_bbmodel.execute(model)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, help="ip address of oscilloscope.")
    parser.add_argument("--email", type=str, help="email address to send notifications for.")
    parser.add_argument("--port", type=int, default=5024, help="port number of oscilloscope.")
    parser.add_argument("--native", action='store_true',help="use native mode for arduino DUE.")
    parser.add_argument('--component', type=str,default=0, help='dac id to evaluate.')




    args = parser.parse_args()

    state = lab_state.State(args.ip,args.port,
                  ard_native=args.native)

    try:

        mgr = modellib.build_manager()
        assert(not args.component is None)
        model = mgr.get(args.component)
        loop(state,model)

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

