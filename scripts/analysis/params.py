import compiler.skelter as skelter
import compiler.common.prop_noise as pnlib
import bmark.menvs as menvs
from enum import Enum

def update_params(conc_circ, \
                  output_entry):
  LOCS = []
  for block_name,loc,config in conc_circ.instances():
    handle = conc_circ.board.handle_by_inst(block_name,loc)
    if handle is None:
      continue

    for port,label,label_kind in config.labels():
      if label == output_entry.varname:
        LOCS.append((block_name,loc,port,handle))

  if len(LOCS) == 0:
    print(output_entry)
    raise Exception("cannot find measurement port")

  if (len(LOCS) > 1):
    raise Exception("more than one port with that label")

  block_name,loc,port,handle = LOCS[0]
  cfg = conc_circ.config(block_name,loc)
  menv = menvs.get_math_env(output_entry.math_env)

  xform = output_entry.transform
  xform.handle = handle
  xform.time_constant = conc_circ.board.time_constant
  xform.legno_ampl_scale = cfg.scf(port)
  xform.legno_time_scale = conc_circ.tau
  output_entry.transform = xform

  runtime = menv.sim_time/(xform.time_constant*xform.legno_time_scale)
  output_entry.runtime = runtime



def analyze(entry,conc_circ):
  params = None
  for output in list(entry.outputs()):
    update_params(conc_circ, \
                           output)

    entry.runtime = output.runtime
