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
    #'K' : 0.000029618,
    'K' : K,
    'nu': 2.0015,
    'beta': 2.5,
    'gamma': 1.0,
    'U0': 0.0,
    'V0': 0.0,
    'kdeg': 0.99999999,
    'one':0.99999
  }
  #reparametrization
  params['a1'] = 0.15;
  params['a2'] = 1.56;
  params
  # derived parameters
  params['invK'] = 1.0/params['K']
  params['negNu'] = -params['nu']
  params['one'] = 0.999999
  prog_util.build_oscillator(prog,params['K'],1.0,"dummy","IPTG")

  prog.decl_lambda("umod","(1+abs(X)*{invK})^{negNu}",params)
  prog.decl_lambda("utf", "{a1}/(1+abs(X)^{beta})",params)
  prog.decl_lambda("vtf", "{a2}/(1+abs(X)^{gamma})",params)


  prog.decl_var("FNUMOD", "umod(IPTG)",params)
  prog.interval("FNUMOD",-1.0,1.0)

  prog.decl_var("UMODIF", "U*FNUMOD",params)
  prog.interval("UMODIF",-0.08,0.08)
  prog.decl_var("UTF", "utf((V))",params)
  prog.interval("UTF",-0.2,0.2)
  prog.decl_var("VTF", "vtf((UMODIF))",params)
  prog.interval("VTF",-1.7,1.7)

  dV = "VTF + {kdeg}*(-V)"
  dU = "UTF + {kdeg}*(-U)"

  prog.decl_stvar("V",dV, "{V0}", params);
  prog.decl_stvar("U",dU, "{U0}", params);
  prog.emit("{one}*UMODIF", "modU", params)

  prog.interval("V",-1.7,1.7)
  prog.interval("U",-0.08,0.08)
  prog.check()
  return


def dssim():
  exp = DSSim('t20')
  exp.set_sim_time(20)
  return exp
