import argparse
import json
import os
import subprocess
import sys

def read_config(cfgfile):
  defaults = {
    'n_abs': 1,
    'n_conc': 1,
    'n_scale': 1,
    'max-freq':None,
    'subset': 'unrestricted',
    'model': 'physical'
  }
  if cfgfile is None:
    return dict(defaults)

  with open(cfgfile,'r') as fh:
    cfg = dict(defaults)
    data = fh.read()
    print(data)
    obj = json.loads(data)
    for k,v in obj.items():
      assert(k in defaults)
      cfg[k] = v

    return cfg

def execute(args,params,logfile):
  argstr = args.format(**params).split(" ")
  cmd = list(filter(lambda q: q != "", \
                    ['python3', 'legno.py']+ argstr))

  cmdstr = " ".join(cmd)
  print(cmdstr)
  try:
    # stdout = subprocess.PIPE lets you redirect the output
    returncode = os.system(cmdstr)
  except OSError:
    print(cmd)
    print("error: popen")
    sys.exit(-1) # if the subprocess call failed, there's not much point in continuing

  if returncode != 0:
    print("error: exit code is nonzero")
    return False
  else:
    return True



parser = argparse.ArgumentParser(description='Legno experiment runner.')

parser.add_argument('--config',
                    help='configuration file to use')
parser.add_argument('--hwenv',default='default',
                    help='default hardware environment')
parser.add_argument('--arco',action='store_true',
                   help='use arco to generate circuits.')
parser.add_argument("--digital-error",default=0.05,type=float, \
                   help="digital percent error")
parser.add_argument("--analog-error",default=0.05,type=float, \
                   help="analog percent error")
parser.add_argument('bmark',
                   help='benchmark to run.')
parser.add_argument("--search",action="store_true", \
                    help="search for minimum percent error")
parser.add_argument("--srcgen",action="store_true", \
                    help="only generate source")



args = parser.parse_args()

params = read_config(args.config)
params['bmark'] = args.bmark
params['hwenv'] = args.hwenv
params['digital_error'] = args.digital_error
params['analog_error'] = args.analog_error
params['search'] = "--search" if args.search else ""

for k,v in params.items():
  print("%s=%s" % (k,v))

arco_args = \
  "--subset {subset} {bmark} arco --xforms 1 --abs-circuits {n_abs} " + \
  "--conc-circuits {n_conc}"
succ = True
if args.arco:
  succ = execute(arco_args,params,'arco.log')

jaunt_args = \
             "--subset {subset} {bmark} jaunt {search} --model {model}  " + \
             "--scale-circuits {n_scale} " + \
             "--digital-error {digital_error} --analog-error {analog_error} "
if not params['max-freq'] is None:
  jaunt_args += " --max-freq %f" % params['max-freq']

if succ and not args.srcgen:
  succ = execute(jaunt_args,params,'jaunt.log')

if succ or args.srcgen:
  graph_args = "--subset {subset} {bmark} graph"
  execute(graph_args,params,'graph.log')

srcgen_args = \
  "--subset {subset} {bmark} srcgen {hwenv} --recompute --trials 1"
succ = execute(srcgen_args,params,'srcgen.log')



