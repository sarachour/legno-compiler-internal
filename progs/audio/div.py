from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.audio.audio_util as audio_util

def dsname():
  return "adiv"

def dsinfo():
  return DSInfo(dsname(), \
                "scale signal",
                "audio output",
                "amplitude")
  info.nonlinear = False
  return info


def dsprog(prog):
  params = {"one":0.999999,"coeff":0.5}
  audio_util.decl_audio_input(prog,"X");
  prog.decl_var("Y", "0.5*X");

  E = "{coeff}*X-{one}*X*Z"
  prog.decl_stvar("Z",E,"1.0",params)
  prog.interval("Z",-2.0,2.0)
  prog.emit("{one}*Z","OUT",params);

def dssim():
  dssim = DSSim('trc');
  dssim.set_sim_time(audio_util \
                     .wall_clock_time(0.1));
  dssim.set_hardware_env("audio")
  return dssim;
