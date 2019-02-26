from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def model():
    K = 40.0
    params = {
        'LacLm0':0,
        'clm0':0,
        'TetRm0':0,
        'LacLp0':0,
        'clp0':0,
        'TetRp0':0,
        'a_tr':0.4995,
        'a0_tr':0.0005,
        'k_tl': 3.01029995664,
        'kd_prot': 0.03010299956,
        'kd_mrna' : 0.15051499783,
        'kf_bind':0.1,
        'kd_bind':0.1/K

    }
    LacLm_ic = 0.5
    clm_ic = 0.25
    TetRm_ic = 0.12

    kd_mrna = 0.15051499783
    a0_tr = 0.0005
    prob = MathProg("repri")

    LacLm  = parse_diffeq('({a0_tr}+Aclp-{kd_mrna}*LacLm)', \
                   'LacLm0',':a',params)

    clm = parse_diffeq('({a0_tr}+ATetRp-{kd_mrna}*clm)', \
                   'clm0',':b',params)

    TetRm = parse_diffeq('({a0_tr}+ALacLp-{kd_mrna}*TetRm)', \
                  'TetRm0',':c',params)

    mrna_bnd = 2.5
    prob.bind("LacLm",LacLm)
    prob.bind("clm",clm)
    prob.bind("TetRm",TetRm)
    prob.set_interval("LacLm",0,mrna_bnd)
    prob.set_interval("clm",0,mrna_bnd)
    prob.set_interval("TetRm",0,mrna_bnd)

    LacLp = parse_diffeq('{k_tl}*LacLm - {kd_prot}*LacLp', \
                  'LacLp0',':d',params)
    clp = parse_diffeq('{k_tl}*clm - {kd_prot}*clp', \
                  'clp0',':e',params)
    TetRp = parse_diffeq('{k_tl}*TetRm - {kd_prot}*TetRp', \
                  'TetRp0',':f',params)

    prot_bnd = 150
    prob.bind("LacLp",LacLp)
    prob.bind("clp",clp)
    prob.bind("TetRp",TetRp)
    prob.set_interval("LacLp",0,prot_bnd)
    prob.set_interval("clp",0,prot_bnd)
    prob.set_interval("TetRp",0,prot_bnd)


    ALacLp = parse_diffeq('{kf_bind}*({a_tr}-ALacLp) - {kd_bind}*ALacLp*LacLp*LacLp',
                   'a_tr',':g',params)

    ATetRp = parse_diffeq('{kf_bind}*({a_tr}-ATetRp) - {kd_bind}*ATetRp*TetRp*TetRp',
                   'a_tr',':g',params)

    Aclp = parse_diffeq('{kf_bind}*({a_tr}-Aclp) - {kd_bind}*Aclp*clp*clp',
                   'a_tr',':g',params)

    prob.bind("ALacLp",ALacLp)
    prob.bind("Aclp",Aclp)
    prob.bind("ATetRp",ATetRp)

    act_bnd = params['a_tr']
    prob.set_interval("ALacLp",0,act_bnd)
    prob.set_interval("Aclp",0,act_bnd)
    prob.set_interval("ATetRp",0,act_bnd)
    prob.set_max_sim_time(2000)
    prob.compile()
    menv = menvs.get_math_env('t2k')
    return menv,prob
