from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.audio.audio_util as audio_util

def dsname():
  return "apass"

def dsinfo():
  return DSInfo(dsname(), \
                "passthru",
                "audio output",
                "amplitude")
  info.nonlinear = False
  return info


def dsprog(prog):
  params = {
    'one':0.9999999
  }
  #prog.emit("{one}*X","OUT",params);
  prog.emit("X","OUT",params);
  audio_util.decl_audio_input(prog,"X");

def dssim():
  dssim = DSSim('trc');
  dssim.set_sim_time(audio_util \
                     .wall_clock_time(0.1));
  dssim.set_hardware_env("audio")
  return dssim;
