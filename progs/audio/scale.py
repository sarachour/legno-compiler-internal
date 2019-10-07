from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.audio.audio_util as audio_util

def dsname():
  return "ascale"

def dsinfo():
  return DSInfo(dsname(), \
                "scale signal",
                "audio output",
                "amplitude")
  info.nonlinear = False
  return info


def dsprog(prog):
  audio_util.decl_audio_input(prog,"X");
  prog.decl_var("Y", "0.5*X");
  prog.emit("Y","OUT");

def dssim():
  dssim = DSSim('trc');
  dssim.set_sim_time(audio_util \
                     .wall_clock_time(0.1));
  dssim.set_hardware_env("audio")
  return dssim;
