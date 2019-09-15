from dslang.dsprog import DSProg
from dslang.dssim import DSSim

def dsname():
  return "bont"

def dsprog(prog):
  scf = 1.0
  scf2 = 3.0
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
    'r_trans_kL': 0.541,
    'r_bind_kB': 0.541,
    'tenB0': 1.0,
    'freeB0': 1.0,
    'bndB0' : 0.0,
    'transB0': 0.0,
    'lyticB0': 0.0,
    'one':0.99999
  }

  dTenB = '{r_trans_kL}*(-transB)'
  prog.decl_stvar("tenb",dTenB,'{tenB0}',params)
  prob.interval('tenB',-1,1)

  dFreeB = '{r_bind_kB}*(-freeB)'
  prob.decl_stvar('freeB',dFreeB,'{freeB0}',params)
  prob.interval('freeB',-1,1)

  dBndB = '{r_bind_kB}*(-freeB) + {r_endo_kT}*(-bndB)'
  prob.decl_stvar('bndB',dBndB, '{bndB0}',params)
  prob.interval('bndB',-1,1)

  dTransB = '{r_endo_kT}*bndB + {r_trans_kL}*(-transB)'
  prob.decl_stvar('transB',dTransB, '{transB0}',params)
  prob.interval('transB',-1,1)

  dLyticB = '{r_trans_kL}*transB'
  prob.decl_stvar('lyticB',dLyricB,'{lyticB0}',params)
  prob.interval('lyticB',-1,1)

  prob.emit('{one}*transB','MTRANSB')


def dssim():
  exp = DSSim('t20')
  exp.set_sim_time(20)
  return exp
