from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.prog_util as prog_util


def dsname():
  return "gentoggle"


def dsprog(prog):
  K = 1.0
  params = {
    'a2': 15.6,
    'a1': 156.25,
    'K' : 0.000029618,
    'nu': 2.0015,
    'beta': 2.5,
    'gamma': 1.0,
    'U0': 0.0,
    'V0': 0.0,
    'kdeg': 0.99999999,
    'vtf_tr':15.6,
    'vtf_kf':1.0,
    'vtf_kd':1.0/K,
    'utf_tr':13.32,
    'utf_kf':1.0,
    'utf_kd':1.0/K
  }
  #reparametrization
  params['K'] *= 10.0;
  params['a1'] = 13.32;
  params
  # derived parameters
  params['invK'] = 1.0/params['K']
  params['negNu'] = -params['nu']
  params['one'] = 0.999999
  prog_util.build_oscillator(prog,params['K'],1.0,"dummy","IPTG")

  prog.decl_lambda("umod","(1+abs(X)*{invK})^{negNu}",params)
  prog.decl_lambda("utf", "{a1}/(1+abs(X)^{beta})",params)
  prog.decl_lambda("vtf", "{a2}/(1+abs(X)^{gamma})",params)


  prog.decl_var("UMODIF", "U*umod(IPTG)")
  prog.decl_var("UTF", "utf(V)")
  prog.decl_var("VTF", "vtf(UMODIF)")

  dV = "VTF + {kdeg}*(-V)"
  dU = "UTF + {kdeg}*(-U)"

  prog.decl_stvar("V",dV, "{V0}", params);
  prog.decl_stvar("U",dU, "{U0}", params);
  prog.emit("{one}*UMODIF", "modU", params)

  prog.interval("UMODIF",0,0.5)
  prog.interval("UTF",0,16.0)
  prog.interval("VTF",0,16.0)
  prog.interval("V",0,16.0)
  prog.interval("U",0,1.5)
  prog.check()
  return


def dssim():
  exp = DSSim('t20')
  exp.set_sim_time(20)
  return exp
