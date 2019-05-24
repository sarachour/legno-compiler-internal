from lang.prog import MathEnv
from ops import op, opparse
import chip.hcdc.globals as glb

def set_microphone(prob,var,mathvar):
  hwfreq = glb.TIME_FREQUENCY
  sound_freq = 22.0*1000.0
  freq = sound_freq/hwfreq
  prob.set_bandwidth(var, freq)
  prob.set_interval(var,-1.0,1.0)
  prob.bind(mathvar, op.ExtVar(var,loc='E1'))

  return -1.0,1.0

def measure_var(prob,invar,outvar):
  prob.bind(outvar,
            op.Emit(op.Mult(op.Const(0.999999), op.Var(invar)), \
                    loc='A0'))

def math_env(prob):
    menv = MathEnv('audenv');
    hwfreq = glb.TIME_FREQUENCY
    time = 0.1
    prob.set_max_sim_time(time*hwfreq)
    menv.set_sim_time(time*hwfreq)
    menv.set_input_time(time*hwfreq)
    return menv
