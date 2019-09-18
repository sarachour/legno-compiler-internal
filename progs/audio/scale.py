from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.audio.audio_util as audio_util

def dsname():
  return "ascale"

def dsprog(prog):
  #prog.decl_extvar("X",loc='E1');
  prog.decl_var("Y", "0.5*X");
  prog.emit("Y","OUT");
  audio_util.decl_audio_input(prog,"X");

def dssim():
  dssim = DSSim('trc');
  dssim.set_sim_time(audio_util \
                     .wall_clock_time(0.1));
  return dssim;
