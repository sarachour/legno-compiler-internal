from dslang.dsprog import DSProg
from dslang.dssim import DSSim

def dsname():
  return "pend"

def dsprog(prog):
  params = {
    "one":0.9999,
    "angvel0":-1.0,
    "ang0":1.0,
    "k1":0.18,
    "k2":0.8
  }
  dVel = "{k1}*(-angvel) + {k2}*sin(ang)";
  dAng = "angvel"
  prog.decl_lambda("sin","-sin(T)");
  prog.decl_stvar("angvel",dVel,"{angvel0}",params);
  prog.decl_stvar("ang",dAng,"{ang0}",params);
  prog.emit("{one}*ang","Angle",params)
  prog.interval('ang', -1.8,1.8)
  prog.interval('angvel',-1.8,1.8)
  prog.check()


def dssim():
  exp = DSSim('t20')
  exp.set_sim_time(20)
  return exp
