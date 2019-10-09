import hwlib.hcdc.globals as glb
import hwlib.units as units

def decl_external_input(prog,name,chan1=True):
  prog.decl_extvar(name,loc='E1' if chan1 else 'E2');
  prog.interval(name,-1,1);
  prog.interval("EXT_%s" % name,-1,1)

def wall_clock_time(wall_time):
  return wall_time*glb.TIME_FREQUENCY

def siggen_time(name):
    # times in seconds, according to signal generator
    times = {
      'sin': 0.01,
      'anomaly-ampl':0.01,
      'anomaly-freq':0.01,
      'heart-normal':0.01,
    }
    return wall_clock_time(times[name]);

def siggen_time_constant(name):
    freqs = {
      'sin': units.khz*40.0,
      'anomaly-freq': units.khz*40.0,
      'anomaly-ampl': units.khz*80.0,
      'heart-normal': units.khz*40.0,
      'heart-irregular': units.khz*80.0,
    }
    return time_constant(freqs[name])

def time_constant(freq):
    hwfreq = glb.TIME_FREQUENCY
    return freq/hwfreq
