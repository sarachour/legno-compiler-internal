if __name__ == "__main__":
    raise Exception("cannot run reference simulation for physical signal")

from lang.prog import MathProg
from lang.prog import MathEnv
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs
import chip.units as units
import chip.hcdc.globals as glb

def model():
    prob = MathProg("aud-lpf")

    params = {
      'tau': 0.5,
      'Z0':0
    }

    # cutoff = 1/(2*pi*RC) = tau*1/(2*pi)
    # tau = 1/RC
    # diffeq: dZ/dt = tau*X - tau*Z
    # we multiply cutoff by capacitor time constant
    # cutoff is 1592 hz (15920 hz?)

    Z = parse_diffeq('{tau}*X + {tau}*(-Z)', 'Z0',':v',params)

    prob.bind('X', op.ExtVar("I",loc='E1'))
    prob.bind('Z', Z)
    prob.bind('OUT',op.Emit(op.Var('Z'), loc='A0'))

    prob.set_bandwidth("I",200*units.khz/glb.TIME_FREQUENCY)
    prob.set_interval("I",-0.25,0.25)
    prob.set_interval("Z",-0.25,0.25)

    time = 0.4
    prob.set_max_sim_time(time*glb.TIME_FREQUENCY)
    prob.compile()

    menv = MathEnv('audenv');
    menv.set_sim_time(time*glb.TIME_FREQUENCY)
    menv.set_input_time(time*glb.TIME_FREQUENCY)
    return menv,prob

