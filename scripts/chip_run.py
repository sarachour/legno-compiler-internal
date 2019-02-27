import sys
import os
import argparse
import chip_compare
import time

sys.path.insert(0,os.path.abspath("lab_bench"))

from util import paths

def ping_user(email,benchmark,script_list):
    msg = "benchmark=%s"
    cmd = "mail -s \"job finished\" %s  <<< \"%s\"" % (email, msg)
    os.system(cmd)

def execute_script(ip,script_file,native=False):
    print(script_file)
    if not ip is None:
        exec_cmd = "python3 lab_bench/arduino_client.py --ip %s --script %s" % (args.ip,script_file)
        exec_cmd += " --native" if native else ""
    else:
        exec_cmd = "python3 lab_bench/arduino_client.py --script %s" % (script_file)
        exec_cmd += " --native" if native else ""

    print(exec_cmd)
    os.system(exec_cmd)
    #print("compare chip result")
    #chip_compare.execute(script_file)
    time.sleep(1)

parser = argparse.ArgumentParser(description='toplevel chip runner.')
parser.add_argument('benchmark', type=str,help='benchmark to compile')
parser.add_argument('--bmark-dir', type=str,default='default',
                       help='directory to output files to.')
parser.add_argument('--script-list', type=str, default=None,
                    help="list of grendel scripts")
parser.add_argument('--ip', type=str,
                       help='oscilloscope ip.')
parser.add_argument('--email', type=str,
                       help='email address.')
parser.add_argument('--native', action='store_true',
                       help='use ttyACM0.')

args = parser.parse_args()

path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
grendel_dir = path_handler.grendel_file_dir()
if args.script_list is None:
    for dirname, subdirlist, filelist in os.walk(grendel_dir):
        for fname in filelist:
            if fname.endswith('.grendel'):
                script_file = "%s/%s" % (dirname,fname)
                execute_script(args.ip,script_file,native=args.native)

else:
    with open(args.script_list,'r') as fh:
        for line in fh:
            if line.startswith("#"):
                continue

            script_file = line.strip()
            execute_script(args.ip,script_file,native=args.native)

if not args.email is None:
    ping_user(args.email,args.benchmark,args.script_list)