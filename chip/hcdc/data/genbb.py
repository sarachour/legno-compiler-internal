import sys
import os
import common
import numpy as np
sys.path.insert(0,os.path.abspath("../../../"))
import chip.phys as phys
import ops.nop as nops
import json

def make_lin(slope,off,deterministic):
    if deterministic:
      return nops.mkadd([
        nops.mkmult([
          nops.NConstVal(slope),
          nops.NFreq(port)
        ]),
        nops.NConstVal(off)
      ])
    else:
      return nops.mkadd([
        nops.mkmult([
          nops.NConstRV(slope),
          nops.NFreq(port)
        ]),
        nops.NConstRV(off)
      ])

def to_nop_expr(indep_dict, dep_dict, break_idx, \
                port, \
                deterministic=False):

  freq = indep_dict['breaks'][break_idx]
  print("freq: %s" % freq)

  if not dep_dict is None:
    dep_slope = dep_dict['slopes'][break_idx]
    dep_offset = dep_dict['offsets'][break_idx]
    dep_expr = nops.mkmult([
      nops.NSig(port),
      make_lin(dep_slope,dep_offset,deterministic)
    ])
    print("dep: %s*F + %s" % (dep_slope,dep_offset))

  indep_slope = indep_dict['slopes'][break_idx]
  indep_offset = indep_dict['offsets'][break_idx]
  print("indep: %s*F + %s" % (indep_slope,indep_offset))

  indep_expr = make_lin(indep_slope,indep_offset, \
                        deterministic)
  if dep_dict is None:
    return indep_expr
  else:
    return nops.mkadd([
      dep_expr,
      indep_expr
    ])




filename = sys.argv[1]
port = sys.argv[2]
breakfile = sys.argv[3]
outfile = sys.argv[4]
breaks = []
with open(breakfile,'r') as fh:
  for line in fh:
    breaks.append(float(line.strip()))

print("=== Read Data ===")
raw_data = common.load_raw_data(filename)
data = common.process_raw_data(raw_data)

print("=== Fit Data ===")
X = raw_data['freqs']
_,model = common.compute_pwls(X,data,extern_breaks=breaks)

print(breaks)
ph = phys.PhysicalModel()
for brk in breaks[:-1]:
  ph.add_break(brk)

ph.freeze()
for idx,this_break in enumerate(breaks[:-1]):
  print("index",idx)
  bias_expr = to_nop_expr(model['ampl_bias_indep'],
                     model['ampl_bias_dep'],
                          idx,
                          port=port,
                          deterministic=True)

  noise_expr = to_nop_expr(model['ampl_noise_indep'],
                           model['ampl_noise_dep'],
                           idx,
                           port=port,
                           deterministic=False)

  delay_mean = to_nop_expr(model['delay_mean'],
                           None,idx,
                           port=port,
                           deterministic=True)

  delay_std = to_nop_expr(model['delay_std'],
                           None,idx,
                           port=port,
                           deterministic=False)

  delay_expr = nops.mkadd([delay_mean,delay_std])

  subm = ph.stump(this_break)
  subm.delay = delay_expr
  subm.noise = noise_expr
  subm.bias = bias_expr


with open(outfile,'w') as fh:
  obj= ph.to_json()
  print(obj)
  objstr = json.dumps(obj,indent=4)
  fh.write(objstr)
