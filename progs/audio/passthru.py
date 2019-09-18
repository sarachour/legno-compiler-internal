from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.audio.audio_util as audio_util

def dsname():
  return "apass"

def dsprog(prog):
  prog.emit("X","OUT");
  audio_util.decl_audio_input(prog,"X");

def dssim():
  dssim = DSSim('trc');
  dssim.set_sim_time(audio_util \
                     .wall_clock_time(0.1));
  return dssim;
