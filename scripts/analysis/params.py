import compiler.skelter as skelter
import compiler.common.prop_noise as pnlib
import bmark.menvs as menvs
from enum import Enum

class RankMethod(Enum):
  SKELTER = "skelter"
  MAXSIGFAST = "maxsigfast"
  MAXSIGSLOW = "maxsigslow"
  SCALE = "scale"
  INTERVAL = "interval"
  HANDTUNED = "handtuned"

def compute_params(conc_circ,entry,varname):
  LOC = None
  for block_name,loc,config in conc_circ.instances():
    handle = conc_circ.board.handle_by_inst(block_name,loc)
    if handle is None:
      continue

    for port,label,label_kind in config.labels():
      if label == varname:
        LOC = (block_name,loc,port)

  block_name,loc,port = LOC
  cfg = conc_circ.config(block_name,loc)
  menv = menvs.get_math_env(entry.math_env)

  params = {}
  params['scf'] = cfg.scf(port)
  params['tau']= (conc_circ.tau)
  params['fmax']= (conc_circ.tau)*conc_circ.board.time_constant
  params['simtime'] = menv.sim_time
  params['runtime'] = params['simtime']/params['fmax']
  return params



def analyze(entry,conc_circ,method=RankMethod.SKELTER):
  params = None
  for output in entry.outputs():
    varname = output.varname
    params = compute_params(conc_circ,entry,
                            varname)
    output.set_tau(params['tau'])
    output.set_fmax(params['fmax'])
    output.set_scf(params['scf'])
    #output.set_rank(RANK)
    print(output)

  if not params is None:
    entry.set_runtime(params['runtime'])
