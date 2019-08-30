if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

def make_output(prob,out,var,adc=False):
  if adc == False:
    prob.bind(out, \
              op.Emit(
                op.Mult(op.Const(0.9999),op.Var(var)),
                loc="A0"
              ))

  else:
    ident_fun = op.Func(['T'], op.Var('T'))
    prob.bind(out,
              op.Emit(op.Call([op.Var(var)], \
                              ident_fun), loc="A0"))


# we introduce an oscillator with gain to better understand how physical models work.
def model_with_gain(menv_name='t20', adc=False):
    omega = 0.75
    params = {
        'P0': 0.1,
        'V0' :0.0,
        'omega': omega*omega
    }
    # t20
    prob = MathProg("micro-osc-with-gain")
    P = parse_diffeq("0.999*V", "P0", ":a", params)
    V = parse_diffeq("{omega}*(-P)", "V0", ":b", params)
    #V = parse_diffeq("{omega}*P", "V0", ":b", params)

    scf = omega
    prob.bind("P", P)
    prob.bind("V", V)
    #make_output(prob,"Loc", "P", adc)
    prob.bind("Pos", \
              op.Emit(op.Var("P"),loc="A0") \
    )

    # most accurately, 0.1
    #base_bnd = 0.1
    base_bnd = 0.12
    prob.set_interval("P",-base_bnd,base_bnd)
    prob.set_interval("V",-base_bnd*scf,base_bnd*scf)
    prob.set_max_sim_time(200)
    prob.compile()
    menv = menvs.get_math_env(menv_name)
    return menv,prob


# from wikipedia
def model(menv_name='t20', adc=False):
    omega = 1.0
    params = {
        'P0': 0.1,
        'V0' :0.0,
        'omega': -1*omega*omega
    }
    # t20
    prob = MathProg("micro-osc")
    P = parse_diffeq("V", "P0", ":a", params)
    V = parse_diffeq("(-P)", "V0", ":b", params)
    #V = parse_diffeq("{omega}*P", "V0", ":b", params)

    scf = omega
    prob.bind("P", P)
    prob.bind("V", V)
    #make_output(prob,"Loc", "P", adc)
    prob.bind("Pos", \
              op.Emit(op.Var("P"),loc="A0") \
    )

    # most accurately, 0.1
    #base_bnd = 0.1
    base_bnd = 0.12
    prob.set_interval("P",-base_bnd,base_bnd)
    prob.set_interval("V",-base_bnd*scf,base_bnd*scf)
    prob.set_max_sim_time(200)
    prob.compile()
    menv = menvs.get_math_env(menv_name)
    return menv,prob

def execute(menv_name='t20'):
  menv,prob = model(menv_name=menv_name)
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
  #execute("quarter",0.25,menv_name='t200')
  #execute("quad",4.0)
1
