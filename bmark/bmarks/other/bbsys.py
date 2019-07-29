if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


def build_std_bb_sys(prob,ampl,index):
  params = {
    'P0': ampl,
    'V0' :0.0,
    'P': "P%d" % index,
    'V': "V%d" % index,
    }
  P = parse_diffeq("{V}", "P0",
                   ":a%d" % index,
                   params)
  V = parse_diffeq("(-{P})", \
                   "V0",
                   ":b%d" % index,
                   params)
  prob.bind(params['P'], P)
  prob.bind(params['V'], V)
  scf = math.sqrt(1.0)
  base_bnd = params['P0']*1.2
  prob.set_interval(params['P'],-base_bnd,base_bnd)
  prob.set_interval(params['V'],-base_bnd*scf,base_bnd*scf)
  return params['P'],params['V']

def build_bb_sys(prob,ampl,omega,index):
  params = {
    'P0': ampl,
    'V0' :0.0,
    'P': "P%d" % index,
    'V': "V%d" % index,
    'O': -omega*omega,
    'one': 0.9999999
  }

  P = parse_diffeq("{one}*{V}", "P0",
                   ":a%d" % index,
                   params)
  V = parse_diffeq("{O}*{P}", \
                   "V0",
                   ":b%d" % index,
                   params)
  prob.bind(params['P'], P)
  prob.bind(params['V'], V)
  scf = math.sqrt(omega)
  base_bnd = params['P0']*1.2
  prob.set_interval(params['P'],-base_bnd,base_bnd)
  prob.set_interval(params['V'],-base_bnd*scf,base_bnd*scf)
  return params['P'],params['V']
'''
DEBUGGING
1. p1 system, one extout - SUCCESS
2. p1 system, two extouts - FAILURE
3. p1 system, two extouts, +const - ?
3. p1 system, two extouts, +self - ?
1. p2 system, one extout - ?
2. p2 system, two extouts - failure
3. p2 system, two extouts, +const - ?
3. p2 system, two extouts, +self - ?


'''
def model():
  prob = MathProg("bbsys")
  ampl,freq = 0.2,0.25
  P1,V1 = build_bb_sys(prob,ampl,freq,0)
  ampl,freq = 0.5,0.16
  P2,V2 = build_bb_sys(prob,ampl,freq,1)

  params = {
    'P1': P1,
    'P2': P2,
    'one': 0.999999
  }
  X = parse_fn('{one}*{P1} + {one}*{P2}',params)
  prob.bind('X', X)
  prob.bind('OUTPUT', op.Emit(op.Var('X')))
  #prob.bind('OUTPUT2', op.Emit(op.Var(P1)))
  prob.set_max_sim_time(200)
  prob.compile()
  menv = menvs.get_math_env('t200')
  return menv,prob

def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
