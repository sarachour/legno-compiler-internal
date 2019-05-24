if __name__ == "__main__":
    raise Exception("cannot run reference simulation for physical signal")

from lang.prog import MathProg
from lang.prog import MathEnv
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs
import chip.units as units
import chip.hcdc.globals as glb
import numpy as np
import bmark.bmarks.audio.audio_util as autil

def model():
    prob = MathProg("aud-lpf")
    prob.set_digital_snr(0.0)
    prob.set_analog_snr(0.0)

    cutoff = 2000
    tc = cutoff/(200*1000.0)*2.0*np.pi
    tc = 0.08
    params = {
        'fill': tc,
        'leak': tc,
        'IC':0
    }

    print("cutoff: %f" % (params['fill']*1/(2*3.14159)*200*1000))
    # cutoff = 1/(2*pi*RC) = tau*1/(2*pi)
    # tau = 1/RC
    # diffeq: dZ/dt = tau*X - tau*Z
    # we multiply cutoff by capacitor time constant
    # cutoff is 1592 hz (15920 hz?)
    lb,ub = autil.set_microphone(prob,"I","X0")
    stages = 8
    for i in range(1,stages):
        E = parse_diffeq('{fill}*X%d + {leak}*(-X%d)' % (i-1,i), \
                         'IC', \
                         ':v%d' % i, \
                         params)

        prob.bind('X%d' % i, E)
        prob.set_interval("X%d" % i,lb,ub)

    autil.measure_var(prob,"X%d" % (stages-1), "OUT")
    menv = autil.math_env(prob)

    prob.compile()
    return menv,prob

