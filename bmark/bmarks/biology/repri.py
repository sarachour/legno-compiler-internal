if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v))


def model(closed_form=True):

  K = 20.0
  params = {
    'LacLm0':0.5,
    'clm0':0.25,
    'TetRm0':0.12,
    'LacLp0':60.0,
    'clp0':20.0,
    'TetRp0':40.0,
    'K':K,
    'n':2.0,
    'a_tr':0.4995,
    'kd_mrna' : 0.15051499783,
    'a0_tr':0.0005,
    'k_tl': 3.01029995664,
    'kd_prot': 0.03010299956,
    'one': 0.9999999,
    'mrna_bnd':3.0,
    'prot_bnd':140.0
  }

  # reparametrization
  K = 1.0
  params = {
    'LacLm0':0.5,
    'clm0':0.25,
    'TetRm0':0.30,
    'LacLp0':6.0,
    'clp0':2.0,
    'TetRp0':4.0,
    'K':K,
    'n':2.0,
    'a_tr':0.75,
    'kd_mrna' : 0.40,
    'a0_tr':0.0,
    'k_tl': 0.901029995664,
    'kd_prot': 0.30,
    'one': 0.9999999,
    'mrna_bnd':1.2,
    'prot_bnd':3.5
  }
  assert(closed_form)
  prob = MathProg("repri")
  LacLm  = parse_diffeq('{a0_tr}+{a_tr}*ALacL+{kd_mrna}*(-LacLm)', \
                        'LacLm0',':a',params)

  clm = parse_diffeq('{a0_tr}+{a_tr}*Aclp+{kd_mrna}*(-clm)', \
                     'clm0',':b',params)
  TetRm = parse_diffeq('{a0_tr}+{a_tr}*ATetR+{kd_mrna}*(-TetRm)', \
                       'TetRm0',':c',params)
  mrna_bnd = params['mrna_bnd']
  prob.bind("LacLm",LacLm)
  prob.bind("clm",clm)
  prob.bind("TetRm",TetRm)
  prob.set_interval("LacLm",0,mrna_bnd)
  prob.set_interval("clm",0,mrna_bnd)
  prob.set_interval("TetRm",0,mrna_bnd)

  LacLp = parse_diffeq('{k_tl}*LacLm + {kd_prot}*(-LacLp)', \
                       'LacLp0',':d',params)
  clp = parse_diffeq('{k_tl}*clm + {kd_prot}*(-clp)', \
                     'clp0',':e',params)
  TetRp = parse_diffeq('{k_tl}*TetRm + {kd_prot}*(-TetRp)', \
                       'TetRp0',':f',params)

  prot_bnd = params['prot_bnd']
  prob.bind("LacLp",LacLp)
  prob.bind("clp",clp)
  prob.bind("TetRp",TetRp)
  prob.set_interval("LacLp",0,prot_bnd)
  prob.set_interval("clp",0,prot_bnd)
  prob.set_interval("TetRp",0,prot_bnd)
  

  K = params['K']
  n = params['n']
  bind_fxn = op.Func(['P'], op.Mult(
    op.Const((K**n)),
    op.Pow(
      op.Add(op.Const(K**n), op.Pow(op.Var('P'), op.Const(n))),
      op.Const(-1.0)
    )
  ))
  if closed_form:
    ALacL = op.Call(
          [op.Var('clp')],
      bind_fxn
    )
    ATetR = op.Call(
      [op.Var('LacLp')],
      bind_fxn
    )
    Aclp = op.Call(
      [op.Var('TetRp')],
      bind_fxn
    )
  else:
    raise Exception("no diffeq impl")

  prob.bind("ALacL",ALacL)
  prob.bind("Aclp",Aclp)
  prob.bind("ATetR",ATetR)
  prob.bind("OBS",emit(op.Var('Aclp')))

  act_bnd = params['a_tr']
  prob.set_interval("ALacL",0,act_bnd)
  prob.set_interval("Aclp",0,act_bnd)
  prob.set_interval("ATetR",0,act_bnd)
  prob.set_max_sim_time(2000)
  prob.compile()
  #menv = menvs.get_math_env('t200')
  menv = menvs.get_math_env('t2k')
  return menv,prob

def execute(closed_form=False):
  menv,prob = model(closed_form=closed_form)
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute(closed_form=True)
  #execute(closed_form=False)
