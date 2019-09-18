import hwlib.hcdc.globals as glb

def decl_audio_input(prog,name):
  prog.decl_extvar("X",loc='E1');
  prog.interval("X",-1,1);

def wall_clock_time(wall_time):
  return wall_time*glb.TIME_FREQUENCY
