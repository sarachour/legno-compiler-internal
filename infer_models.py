import argparse
import sys
import os
import shutil
import util.config as CONFIG
from chip.model import ModelDB
import json
#import lab_bench.lib.chipcmd.data as chipcmd
#import itertools
#import numpy as np
#import math
#from chip.model import PortModel, ModelDB
#from chip.hcdc.globals import HCDCSubset
#from scipy import optimize

import compiler.infer_pass.infer_dac as infer_dac
import compiler.infer_pass.infer_fanout as infer_fanout
import compiler.infer_pass.infer_integ as infer_integ
import compiler.infer_pass.infer_mult as infer_mult

db = ModelDB()

def build_model(obj):
  for datum in obj:
    blk = datum['metadata']['block']
    if blk == 'dac':
      for model in infer_dac.infer(datum):
        db.put(model)

    elif blk == 'fanout':
      infer_fanout.infer(datum)
    elif blk == 'integ':
      infer_integ.infer(datum)
    elif blk == 'mult':
      for model in infer_mult.infer(datum):
        db.put(model)
    else:
      raise Exception("unsupported <%s>" % blk)

cmd = "python3 grendel.py --dump-db calibrate.grendel"
print(cmd)
retcode = os.system(cmd)
if retcode != 0:
  raise Exception("could not dump database: retcode=%d" % retcode)

for dirname, subdirlist, filelist in os.walk(CONFIG.DATASET_DIR):
  for fname in filelist:
    if fname.endswith('.json'):
      fpath = "%s/%s" % (dirname,fname)
      with open(fpath,'r') as fh:
        obj = json.loads(fh.read())
        build_model(obj)
