from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.prog_util as prog_util

def dsname():
  return "pid"

def dsprog(prog):
  params = {
      "target": 0.2,
      "initial": 1.0
  }

  ampl = 1.0
  freq = 0.2
  prog_util.build_oscillator(prog,ampl,freq,"Z0","Z1")
  SIGNAL = "Z0+Z1"
  PLANT = "CTRL+0.1*SIG"
  ERROR = "VEL-{target}"
  CONTROL = "0.6*(-ERR)+0.5*(-INTEG)"
  INTEGRAL = "ERR-0.1*INTEG"

  prob.decl_var("SIG",SIGNAL,params)
  prob.decl_var("ERR",ERROR,params)
  prob.decl_var("CTRL",CONTROL,params)
  prob.decl_stvar("INTEG",INTEGRAL,"{initial}",params)
  prob.decl_stvar("PLANT",PLANT,"{initial}",params)

  prob.bind("Error", "{one}*ERR")
  for v in ['SIGNAL','PLANT','CONTROL','ERROR','INTEG']:
    prob.interval(v,-1,1)

  prob.check()

def dssim():
  exp = DSSim('t200')
  exp.set_sim_time(200)
  return exp
