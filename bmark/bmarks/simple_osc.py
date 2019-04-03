if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

# from wikipedia
def model(name,omega,menv_name='t20'):
    params = {
        'P0': 0.1,
        'V0' :0.0,
        'omega': -1*omega*omega
    }
    # t20
    prob = MathProg("micro-osc-%s" % name)
    prob.set_digital_snr(10.0)
    P = parse_diffeq("V", "P0", ":a", params)
    V = parse_diffeq("{omega}*P", "V0", ":b", params)

    scf = omega
    prob.bind("P", P)
    prob.bind("V", V)
    prob.bind("Loc", op.Emit(
      op.Mult(op.Const(0.9999),op.Var("P"))
    ))
    # most accurately, 0.1
    #base_bnd = 0.1
    base_bnd = 0.12
    prob.set_interval("P",-base_bnd,base_bnd)
    prob.set_interval("V",-base_bnd*scf,base_bnd*scf)
    prob.set_max_sim_time(200)
    prob.compile()
    menv = menvs.get_math_env(menv_name)
    return menv,prob

def execute(name,omega,menv_name='t20'):
  menv,prob = model(name,omega, \
                    menv_name=menv_name)
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute("one",1.0)
  execute("quarter",0.25,menv_name='t200')
  execute("quad",4.0)
1
