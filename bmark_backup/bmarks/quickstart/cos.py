if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


# from wikipedia
def model():
    params = {
        'p(0)': 1.0,
        'v(0)' :0.0
    }
    # t20
    prob = MathProg("cos")
    p = parse_diffeq("v", "p(0)", ":a", params)
    v = parse_diffeq("(-p)", "v(0)", ":b", params)
    #V = parse_diffeq("{omega}*P", "V0", ":b", params)

    prob.bind("p", p)
    prob.bind("v", v)
    #make_output(prob,"Loc", "P", adc)
    prob.bind("pos", \
              op.Emit(op.Var("p"),loc="A0") \
    )

    # most accurately, 0.1
    #base_bnd = 0.1
    base_bnd = 1.0
    prob.set_interval("p",-1,1)
    prob.set_interval("v",-1,1)
    prob.set_max_sim_time(200)
    prob.compile()
    menv = menvs.get_math_env('t20')
    return menv,prob

