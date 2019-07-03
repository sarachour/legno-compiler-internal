if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.bmarks.other.bbsys as bbsys
import bmark.menvs as menvs


def model():
  K = 1.0
  params = {
    'a2': 15.6,
    'a1': 156.25,
    'K' : 0.000029618*10.0,
    #'K' : 0.000029618,
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
  prob = MathProg("gentoggle")
  pos,vel = bbsys.build_bb_sys(prob,params['K'],1.0,0)
  umodif_fun = op.Func(['X'],
                       op.Div(
                         op.Const(1.0),
                         op.Pow(
                           op.Add(
                             op.Const(1.0),
                             op.Mult(
                               op.Const(1.0/params['K']),
                               op.Abs(op.Var('X'))
                             )
                           ),
                           op.Const(params['nu'])
                         )
                       ))
  UTF_fun = op.Func(['X'],
                    op.Div(
                      op.Const(params['a1']),
                      op.Add(
                        op.Const(1.0),
                        op.Pow(op.Var('X'), \
                               op.Const(params['beta']))
                      )
                    )
  )
  VTF_fun = op.Func(['X'],
                    op.Div(
                      op.Const(params['a2']),
                      op.Add(
                        op.Const(1.0),
                        op.Pow(op.Var('X'), \
                               op.Const(params['gamma']))
                      )
                    )
  )
  prob.bind("IPTG",op.Var(pos))
  prob.bind("umodif",op.Call([op.Var('P0')], umodif_fun))
  prob.set_interval("umodif",0.0,1.0)

  #to_beta = op.Func(['P'], op.Pow(op.Var('P'),op.Const(params['beta'])))
  #Vbeta = op.Call([op.Var('V')], to_beta)
  #prob.bind("Vbeta",Vbeta)
  #params['utf_tr_kf'] = params['utf_tr']*params['utf_kf']
  #UTF = parse_diffeq('{utf_tr_kf}+{utf_kf}*(-UTF) + {utf_kd}*(-UTF)*Vbeta',
  #                   'utf_tr',':utf',params)
  #prob.bind("UTF",UTF)
  prob.bind("UTF",op.Call([op.Var('V')], UTF_fun))
  prob.set_interval("UTF",0.0,params['utf_tr'])

  #params['vtf_tr_kf'] = params['vtf_tr']*params['vtf_kf']
  #VTF = parse_diffeq('{vtf_tr_kf}+{vtf_kf}*(-VTF) + {vtf_kd}*(-VTF)*umodif',
  #                     'vtf_tr',':vtf',params)

  #prob.bind("VTF",VTF)
  prob.bind("VTF",op.Call([op.Var('umodif')], VTF_fun))
  prob.set_interval("VTF",0.0,params['vtf_tr'])

  V = parse_diffeq("VTF+{kdeg}*(-V)","U0",":v", params)
  prob.bind("V",V)
  prob.set_interval("V",0,13.32)
  U = parse_diffeq("UTF+{kdeg}*(-U)",'V0',":u", params)
  prob.bind("U",U)
  prob.set_interval("U",0,15.6)
  prob.bind("VOUT",op.Emit(op.Var('V'),loc="A0"))
  prob.set_max_sim_time(20)
  prob.compile()
  menv = menvs.get_math_env('t20')
  return menv,prob


def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
