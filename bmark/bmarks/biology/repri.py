if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def emit(v):
  return op.Emit(op.Mult(op.Const(0.99999), v),loc="A0")


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
  K = 0.35
  scale = 1.0
  params = {
    'LacLm0':0.5,
    'clm0':0.25,
    'TetRm0':0.12,
    'LacLp0':0.6,
    'clp0':0.2,
    'TetRp0':0.4,
    'K':K,
    'n':2.0,
    'a_tr':0.99,
    'kd_mrna' : 0.40,
    'k_tl': 0.201029995664,
    'kd_prot': 0.30,
    'one': 0.9999999,
    'mrna_bnd':1.3*scale,
    'prot_bnd':0.85*scale,
    'gene_bnd':1.0
  }
  if not closed_form:
    prob = MathProg("crepri")
  else:
    prob = MathProg("repri")

    ##
  #LacLm  = parse_diffeq('{a0_tr}+{a_tr}*ALacL+{kd_mrna}*(-LacLm)', \
  #                      'LacLm0',':a',params)
  LacLm  = parse_diffeq('{a_tr}*ALacL+{kd_mrna}*(-LacLm)', \
                        'LacLm0',':a',params)

  clm = parse_diffeq('{a_tr}*Aclp+{kd_mrna}*(-clm)', \
                     'clm0',':b',params)
  TetRm = parse_diffeq('{a_tr}*ATetR+{kd_mrna}*(-TetRm)', \
                       'TetRm0',':c',params)
  prob.bind("LacLm",LacLm)
  prob.bind("clm",clm)
  prob.bind("TetRm",TetRm)
  mrna_bnd = params['mrna_bnd']
  prob.set_interval("LacLm",0,mrna_bnd)
  prob.set_interval("clm",0,mrna_bnd)
  prob.set_interval("TetRm",0,mrna_bnd)

  LacLp = parse_diffeq('{k_tl}*LacLm + {kd_prot}*(-LacLp)', \
                       'LacLp0',':d',params)
  clp = parse_diffeq('{k_tl}*clm + {kd_prot}*(-clp)', \
                     'clp0',':e',params)
  TetRp = parse_diffeq('{k_tl}*TetRm + {kd_prot}*(-TetRp)', \
                       'TetRp0',':f',params)

  prob.bind("LacLp",LacLp)
  prob.bind("clp",clp)
  prob.bind("TetRp",TetRp)
  prot_bnd = params['prot_bnd']
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
    prob.bind("ALacL",ALacL)
    prob.bind("Aclp",Aclp)
    prob.bind("ATetR",ATetR)
  else:
    subparams = {
      'Kd': 1.0/(K**n),
      'speed':4.0
    }
    subparams['kf'] = subparams['Kd']*subparams['speed']
    subparams['kr'] = params['one']*subparams['speed']
    subparams['L0'] = 1.0

    # L' = kr*(L0-L) - kf*P*P*L
    def mkrxn(prot,name):
      subparams['L'] = "A%s" % name
      subparams['P'] = prot
      subparams['one'] = 0.9999999
      subparams['krL0'] = subparams['kr']*subparams['L0']
      expr = "{krL0}+{kr}*(-{L}) + {kf}*({one}*{P}*{P})*(-{L})"
      eqn = parse_diffeq(expr, \
                         'L0', \
                         ':l%s'%prot, \
                         subparams)
      prob.bind(subparams['L'],eqn)
      prob.set_interval(subparams['L'],0,subparams['L0'])

    mkrxn(prot="clp",name='LacL')
    mkrxn(prot="LacLp",name='TetR')
    mkrxn(prot="TetRp",name='clp')

  prob.bind("OBS",emit(op.Var('LacLp')))

  act_bnd = params['gene_bnd']
  prob.set_interval("ALacL",0,act_bnd)
  prob.set_interval("Aclp",0,act_bnd)
  prob.set_interval("ATetR",0,act_bnd)
  prob.set_max_sim_time(200)
  prob.compile()
  #menv = menvs.get_math_env('t200')
  menv = menvs.get_math_env('t200')
  return menv,prob

def execute(closed_form=False):
  menv,prob = model(closed_form=closed_form)
  plot_diffeq(menv,prob)


if __name__ == "__main__":
  execute(closed_form=True)
  execute(closed_form=False)
