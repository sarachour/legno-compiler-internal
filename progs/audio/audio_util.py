import hwlib.hcdc.globals as glb

def decl_audio_input(prog,name,chan1=True):
  prog.decl_extvar(name,loc='E1' if chan1 else 'E2');
  prog.interval(name,-1,1);
  prog.interval("EXT_%s" % name,-1,1)

def wall_clock_time(wall_time):
  return wall_time*glb.TIME_FREQUENCY

def hwclock_frequency(freq):
    hwfreq = glb.TIME_FREQUENCY
    return freq/hwfreq
