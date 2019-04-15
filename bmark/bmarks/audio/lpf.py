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
        'fill': 0.08,
        'leak': 0.08,
        'IC':0
    }

    # cutoff = 1/(2*pi*RC) = tau*1/(2*pi)
    # tau = 1/RC
    # diffeq: dZ/dt = tau*X - tau*Z
    # we multiply cutoff by capacitor time constant
    # cutoff is 1592 hz (15920 hz?)

    prob.bind('X0', op.ExtVar("I",loc='E1'))
    bw = 20*units.khz/glb.TIME_FREQUENCY
    ampl = 0.5
    prob.set_bandwidth("I",bw)
    prob.set_interval("I",-ampl,ampl)
    stages = 8
    for i in range(1,stages):
        E = parse_diffeq('{fill}*X%d + {leak}*(-X%d)' % (i-1,i), \
                         'IC', \
                         ':v%d' % i, \
                         params)

        prob.bind('X%d' % i, E)
        prob.set_interval("X%d" % i,-ampl,ampl)

    prob.bind('OUT',op.Emit(op.Var('X%d' % (stages-1)), loc='A0'))

    time = 0.1
    prob.set_max_sim_time(time*glb.TIME_FREQUENCY)
    prob.compile()

    menv = MathEnv('audenv');
    menv.set_sim_time(time*glb.TIME_FREQUENCY)
    menv.set_input_time(time*glb.TIME_FREQUENCY)
    return menv,prob

