if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


# from wikipedia
def model(menv_name='t20', adc=False):
    omega = 1.0
    params = {
        'P0': 0.1,
        'V0' :0.0,
        'omega': -1*omega*omega
    }
    # t20
    prob = MathProg("cos")
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

