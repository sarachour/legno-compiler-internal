from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.prog_util as prog_util

def dsname():
  return "kalconst"

def dsprog(prog):
  params = {
    'meas_noise':0.02,
    'proc_noise':0.02,
    'mean':0.5,
    'one':0.9999
  }

  ampl = 0.5
  freq = 0.1
  prog_util.build_oscillator(prog,ampl,freq,"dummy","SIG")
  params['meas_noise_inv'] = 1.0/params['meas_noise']
  params['X0'] = 0.0
  params['P0'] = 0.05

  dX = "{meas_noise_inv}*P*(SIG-X)"
  dP = "{proc_noise}-{meas_noise_inv}*P*P"

  prog.decl_stvar("X",dX,"{X0}",params)
  prog.decl_stvar("P",dP,"{P0}",params)
  prog.emit("{one}*X","STATE",params)
  prog.interval("X",0,1.0)
  prog.interval("P",0,0.1)

def dssim():
  exp = DSSim('t50')
  exp.set_sim_time(50)
  return exp
