from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs

# from wikipedia
def model(name,omega):
    params = {
        'P0': 0.1,
        'V0' :0.0,
        'omega': -1*omega*omega
    }
    # t20
    prob = MathProg("micro-osc-%s" % name)
    P = parse_diffeq("V", "P0", ":a", params)
    V = parse_diffeq("{omega}*P", "V0", ":b", params)

    scf = omega if omega >= 1.0 else 1.0
    prob.bind("P", P)
    prob.bind("V", V)
    prob.bind("Loc", op.Emit(op.Var("P")))
    # most accurately, 0.1
    #base_bnd = 0.1
    base_bnd = 0.12
    prob.set_interval("P",-base_bnd,base_bnd)
    prob.set_interval("V",-base_bnd*scf,base_bnd*scf)
    prob.compile()
    menv = menvs.get_math_env('t20')
    return menv,prob
