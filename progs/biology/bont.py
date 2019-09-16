from dslang.dsprog import DSProg
from dslang.dssim import DSSim

def dsname():
  return "bont"

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
    'lyticB0': 0.0
  }
  # reparametrization
  params = {
    'r_endo_kT': 0.541,
    'r_trans_kL': 0.1,
    'r_bind_kB': 0.25,
    'tenB0': 1.0,
    'freeB0': 1.0,
    'bndB0' : 0.0,
    'transB0': 0.0,
    'lyticB0': 0.0,
    'one':0.999999
  }
  # reparametrization

  dTenB = '{r_trans_kL}*(-transB)'
  prog.decl_stvar("tenB",dTenB,'{tenB0}',params)
  prog.interval('tenB',-2,2)

  dFreeB = '{r_bind_kB}*(-freeB)'
  prog.decl_stvar('freeB',dFreeB,'{freeB0}',params)
  prog.interval('freeB',-1,1)

  dBndB = '{r_bind_kB}*(-freeB) + {r_endo_kT}*(-bndB)'
  prog.decl_stvar('bndB',dBndB, '{bndB0}',params)
  prog.interval('bndB',-1,1)

  dTransB = '{r_endo_kT}*bndB + {r_trans_kL}*(-transB)'
  prog.decl_stvar('transB',dTransB, '{transB0}',params)
  prog.interval('transB',-1,1)

  dLyticB = '{r_trans_kL}*transB'
  prog.decl_stvar('lyticB',dLyticB,'{lyticB0}',params)
  prog.interval('lyticB',-1,1)

  prog.emit('{one}*transB','MTRANSB',params)
  prog.check()

def dssim():
  exp = DSSim('t20')
  exp.set_sim_time(20)
  return exp
