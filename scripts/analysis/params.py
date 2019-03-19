import compiler.skelter as skelter
import compiler.common.prop_noise as pnlib
import bmark.menvs as menvs

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
  scf = cfg.scf(port)
  tau = (conc_circ.tau)
  fmax = (conc_circ.tau)*conc_circ.board.time_constant

  skelter.clear_noise_model(conc_circ)
  pnlib.compute(conc_circ)
  snr = skelter.snr(conc_circ,block_name,loc,port)
  menv = menvs.get_math_env(entry.math_env)
  simtime = menv.sim_time
  runtime = simtime/fmax
  return snr,tau,fmax,scf,runtime


def analyze(entry,conc_circ):
  for output in entry.outputs():
    varname = output.varname
    RANK,TAU,FMAX,SCF,RUNTIME = compute_params(conc_circ,entry,varname)
    output.set_rank(RANK)
    output.set_tau(TAU)
    output.set_fmax(FMAX)
    output.set_scf(SCF)

  entry.set_runtime(RUNTIME)

  RANK = skelter.rank(conc_circ)
  entry.set_rank(RANK)
