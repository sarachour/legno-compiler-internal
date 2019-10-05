from dslang.dsprog import DSProg
from dslang.dssim import DSSim

def dsname():
  return "bont"

def dsinfo():
  return DSInfo(dsname(), \
                "bont",
                "signal",
                "signal")
  info.nonlinear = True
  return info



def dsprog(prog):
  # original set of parameters
  params = {
    'r_endo_kT': 0.141,
    'r_trans_kL': 0.013,
    'r_bind_kB': 0.058,
    'tenB0': 1.0,
    'freeB0': 1.0,
    'bndB0' : 0.0,
    'transB0': 0.0,
    'lyticB0': 0.0,
    'one':0.999999
  }
  # reparametrization
  scale = 20.0
  params = {
    'r_endo_kT': 0.141*scale*0.7,
    'r_trans_kL': 0.013*scale,
    'r_bind_kB': 0.058*scale,
    'tenB0': 0.0,
    'freeB0': 10.0,
    'bndB0' : 0.0,
    'transB0': 0.0,
    'lyticB0': 0.0,
    'one':0.999999
  }
  # reparametrization

  base = 10.0
  b = 1.0*base
  dTenB = '{r_trans_kL}*(-transB)'
  prog.decl_stvar("tenB",dTenB,'{tenB0}',params)
  prog.interval('tenB',-b,b)

  b = 1.0*base
  dFreeB = '{r_bind_kB}*(-freeB)'
  prog.decl_stvar('freeB',dFreeB,'{freeB0}',params)
  prog.interval('freeB',-b,b)

  #b = 0.3*base
  b = 1.0*base
  dBndB = '{r_bind_kB}*(-freeB) + {r_endo_kT}*(-bndB)'
  prog.decl_stvar('bndB',dBndB, '{bndB0}',params)
  prog.interval('bndB',-b,b)

  #b = 0.7*base
  b = 1.0*base
  dTransB = '{r_endo_kT}*bndB + {r_trans_kL}*(-transB)'
  prog.decl_stvar('transB',dTransB, '{transB0}',params)
  prog.interval('transB',-b,b)

  b = 1.0*base
  dLyticB = '{r_trans_kL}*transB'
  prog.decl_stvar('lyticB',dLyticB,'{lyticB0}',params)
  prog.interval('lyticB',-b,b)

  prog.emit('{one}*transB','MTRANSB',params)
  prog.check()

def dssim():
  exp = DSSim('t20')
  exp.set_sim_time(20)
  return exp
