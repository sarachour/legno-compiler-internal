import hwlib.hcdc.globals as glb

def decl_audio_input(prog,name,chan1=True):
  prog.decl_extvar("X",loc='E1' if chan1 else 'E2');
  prog.interval("X",-1,1);

def wall_clock_time(wall_time):
  return wall_time*glb.TIME_FREQUENCY
