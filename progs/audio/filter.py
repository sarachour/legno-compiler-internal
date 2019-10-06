import progs.audio.audio_util as audio_util
import progs.audio.filter_util as filter_util
from dslang.dssim import DSSim
from dslang.dsprog import DSProg

def dsname():
  return "afilter"

def dsinfo():
  return DSInfo(dsname(), \
                "filter",
                "audio output",
                "amplitude")
  info.nonlinear = False
  return info


def dsprog(prog):
  params = {
    "one": 0.99999
  }
  audio_util.decl_audio_input(prog,"X");
  cutoff_freq = 20000
  degree = 1
  out,model = filter_util.lpf(invar="X", \
                              outvar="Z", \
                              method=filter_util.FilterMethod.BASIC, \
                              cutoff_freq=cutoff_freq, \
                              degree=degree)

  filter_util.model_to_diffeqs(prog,model,1.0)
  prog.emit("{one}*%s" % out,"OUT",params);
  print(prog)

def dssim():
  dssim = DSSim('trc');
  dssim.set_sim_time(audio_util \
                     .wall_clock_time(0.1));
  dssim.set_hardware_env("audio")
  return dssim;
