from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.prog_util as prog_util

def dsname():
  return "pid"

def dsprog(prob):
  params = {
    "target": 0.2,
    "initial": 1.0,
    "one":0.99999
  }

  ampl = 1.0
  freq = 0.2

  params['negTarget'] = -params['target']
  prog_util.build_oscillator(prob,ampl,freq,"Z0","Z1")
  SIGNAL = "Z0+Z1"
  PLANT = "CTRL+0.1*SIG"
  ERROR = "PLANT+({negTarget})"
  CONTROL = "0.8*(-ERR)+1.7*(-INTEG)"
  INTEGRAL = "ERR-0.1*INTEG"

  prob.decl_var("SIG",SIGNAL,params)
  prob.decl_var("ERR",ERROR,params)
  prob.decl_var("CTRL",CONTROL,params)
  prob.decl_stvar("INTEG",INTEGRAL,"{initial}",params)
  prob.decl_stvar("PLANT",PLANT,"{initial}",params)

  prob.emit("{one}*ERR","Error",params)
  for v in ['SIG','PLANT','CTRL','ERR','INTEG']:
    prob.interval(v,-1,1)

  print(prob)
  prob.check()

def dssim():
  exp = DSSim('t200')
  exp.set_sim_time(200)
  return exp
