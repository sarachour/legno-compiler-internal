from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.prog_util as prog_util

def dsname():
  return "kalconst"

def dsinfo():
  info = DSInfo(dsname(), \
                "average tracking kalman filter",
                "average",
                "ampl")
  info.nonlinear = True
  return info

def dsprog(prog):
  params = {
    'meas_noise':0.5,
    'proc_noise':0.9999,
    'one':0.9999
  }

  ampl = 1.0
  freq = 0.3
  prog_util.build_oscillator(prog,ampl,freq,"dummy","SIG")
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -1.0/params['proc_noise']
  params['X0'] = 0.0
  params['P0'] = 1.0
  params['Q'] = params['meas_noise']

  #prog.decl_lambda("pos","max(X,0)");
  #prog.decl_lambda("posq","max((X*X),0)");
  E = "SIG+{one}*(-X)"
  dX = "{Rinv}*P*E"
  dP = "{Q}+{nRinv}*P*P"

  #dX = "{Rinv}*PP*E"
  #dP = "{Q}+{Rinv}*PSQ"

  #prog.decl_var("PSQ","-posq(P)",params)
  #prog.decl_var("PP","pos(P)",params)
  prog.decl_var("E",E,params)
  prog.decl_stvar("X",dX,"{X0}",params)
  prog.decl_stvar("P",dP,"{P0}",params)
  prog.emit("{one}*X","STATE",params)
  prog.interval("X",0,1.0)
  prog.interval("P",0,1.0)

def dssim():
  exp = DSSim('t50')
  exp.set_sim_time(50)
  return exp
