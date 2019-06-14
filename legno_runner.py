import argparse
import json
import os
import subprocess
import sys

def read_config(cfgfile):
  defaults = {
    'n_abs': 1,
    'n_conc': 3,
    'n_scale': 1,
    'sweep': True,
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

    if cfg['sweep']:
      cfg['sweep'] = "--sweep"
    else:
      cfg['sweep'] = ""

    return cfg

def execute(args,params,logfile):
  argstr = args.format(**params).split(" ")
  cmd = ['python3', 'legno.py']+ argstr
  print(" ".join(cmd))
  try:
    # stdout = subprocess.PIPE lets you redirect the output
    res = subprocess.Popen(cmd, stdout=subprocess.PIPE)
  except OSError:
    print(cmd)
    print("error: popen")
    sys.exit(-1) # if the subprocess call failed, there's not much point in continuing

  res.wait()
  # access the output from stdout
  result = res.stdout.read()
  with open(logfile,'w') as fh:
    for line in result.strip().decode().splitlines():
      fh.write("%s\n" % line)

  if res.returncode != 0:
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
parser.add_argument('bmark',
                   help='benchmark to run.')


args = parser.parse_args()

params = read_config(args.config)
params['bmark'] = args.bmark
params['hwenv'] = args.hwenv

for k,v in params.items():
  print("%s=%s" % (k,v))

arco_args = \
  "--subset {subset} {bmark} arco --xforms 1 --abs-circuits {n_abs} " + \
  "--conc-circuits {n_conc}"
succ = True
if args.arco:
  succ = execute(arco_args,params,'arco.log')

jaunt_args = \
  "--subset {subset} {bmark} jaunt --model {model} --scale-circuits {n_scale} {sweep}"
if succ:
  execute(jaunt_args,params,'jaunt.log')

srcgen_args = \
  "--subset {subset} {bmark} srcgen {hwenv} --recompute"
if succ:
  execute(srcgen_args,params,'srcgen.log')



