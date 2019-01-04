import sys
import os
import argparse
import chip_compare

sys.path.insert(0,os.path.abspath("lab_bench"))

from util import paths


parser = argparse.ArgumentParser(description='toplevel chip runner.')
parser.add_argument('benchmark', type=str,help='benchmark to compile')
parser.add_argument('--bmark-dir', type=str,default='default',
                       help='directory to output files to.')
parser.add_argument('ip', type=str,
                       help='oscilloscope ip.')



args = parser.parse_args()

path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
grendel_dir = path_handler.grendel_file_dir()
for dirname, subdirlist, filelist in os.walk(grendel_dir):
    for fname in filelist:
        if fname.endswith('.grendel'):
          script_file = "%s/%s" % (dirname,fname)
          print(script_file)
          exec_cmd = "python3 lab_bench/arduino_client.py --ip %s --script %s" % (args.ip,script_file)
          print(exec_cmd)
          os.system(exec_cmd)
          print("compare chip result")
          chip_compare.execute(script_file)
          input()
