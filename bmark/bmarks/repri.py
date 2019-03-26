if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def model():
    K = 20.0
    params = {
        'LacLm0':0.5,
        'clm0':0.25,
        'TetRm0':0.12,
        #'LacLp0':60.0,
        #'clp0':20.0,
        #'TetRp0':40.0,
        'LacLp0':60.0*0.1,
        'clp0':20.0*0.1,
        'TetRp0':40.0*0.1,
        'K':K,
        'n':2.0,
        'a_tr':0.4995,
        'kd_mrna' : 0.15051499783,
        #'a0_tr':0.0005,
        'a0_tr':0.0,
        'k_tl': 3.01029995664,
        #'k_tl': 3.01029995664*0.05,
        #'kd_prot': 0.03010299956*0.5,
        'kd_prot': 0.03010299956,
        'kf_bind':1.0,
        'kd_bind':1.0/K

    }

    prob = MathProg("repri")

    LacLm  = parse_diffeq('{a0_tr}+ALacL+{kd_mrna}*(-LacLm)', \
                   'LacLm0',':a',params)

    clm = parse_diffeq('{a0_tr}+Aclp+{kd_mrna}*(-clm)', \
                   'clm0',':b',params)

    TetRm = parse_diffeq('{a0_tr}+ATetR+{kd_mrna}*(-TetRm)', \
                  'TetRm0',':c',params)

    mrna_bnd = 2.5
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

    prot_bnd = 13.0
    prob.bind("LacLp",LacLp)
    prob.bind("clp",clp)
    prob.bind("TetRp",TetRp)
    prob.set_interval("LacLp",0,prot_bnd)
    prob.set_interval("clp",0,prot_bnd)
    prob.set_interval("TetRp",0,prot_bnd)

    K = params['K']
    n = params['n']
    bind_fxn = op.Func(['P'], op.Mult(
        op.Const((K**n)*params['a_tr']),
        op.Pow(
            op.Add(op.Const(K**n), op.Pow(op.Var('P'), op.Const(n))),
            op.Const(-1.0)
        )
    ))
    closed_form = False
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
        params['a_tr_kf_bind'] = params['a_tr']*params['kf_bind']
        ALacL = parse_diffeq('{a_tr_kf_bind}+{kf_bind}*(-ALacL) + {kd_bind}*(-ALacL)*clp*clp',
                    'a_tr',':g',params)

        ATetR = parse_diffeq('{a_tr_kf_bind}+{kf_bind}*(-ATetR) + {kd_bind}*(-ATetR)*LacLp*LacLp',
                    'a_tr',':h',params)

        Aclp = parse_diffeq('{a_tr_kf_bind}+{kf_bind}*(-Aclp) + {kd_bind}*(-Aclp)*TetRp*TetRp',
                    'a_tr',':i',params)
    prob.bind("ALacL",ALacL)
    prob.bind("Aclp",Aclp)
    prob.bind("ATetR",ATetR)

    act_bnd = params['a_tr']
    prob.set_interval("ALacL",0,act_bnd)
    prob.set_interval("Aclp",0,act_bnd)
    prob.set_interval("ATetR",0,act_bnd)
    prob.set_max_sim_time(2000)
    prob.compile()
    #menv = menvs.get_math_env('t200')
    menv = menvs.get_math_env('t2k')
    return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
