from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.audio.audio_util as audio_util

def dsname():
  return "adenoise"

def dsinfo():
  return DSInfo(dsname(), \
                "denoise",
                "audio output",
                "amplitude")
  info.nonlinear = False
  return info


def dsprog(prog):
  tc = 10.0
  params = {
    'meas_noise':1.0,
    'proc_noise':0.9999,
    'one':0.9999,
    'tc':0.1
  }
  audio_util.decl_audio_input(prog,"SIG");
  params['Rinv'] = 1.0/params['proc_noise']
  params['nRinv'] = -1.0/params['proc_noise']
  params['X0'] = 0.0
  params['P0'] = 0.0
  params['Q'] = params['meas_noise']

  E = "SIG+{one}*(-X)"
  dX = "{tc}*RP*E"
  dP = "{tc}*(-RP)*P"
  prog.decl_var("RP","{Rinv}*P",params)
  prog.decl_var("E",E,params)
  prog.decl_stvar("X",dX,"{X0}",params)
  prog.decl_stvar("P",dP,"{P0}",params)
  prog.interval("X",-1.0,1.0)
  prog.interval("P",0,1.0)
  prog.emit("{one}*X","STATE",params)


def dssim():
  dssim = DSSim('trc');
  dssim.set_sim_time(audio_util \
                     .wall_clock_time(0.1));
  return dssim;
