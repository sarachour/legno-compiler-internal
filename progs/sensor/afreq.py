from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.sensor.sensor_util as sensor_util
import hwlib.units as units

'''
def ext(t):
    x =  math.sin(0.1*t)
    if t > 20 and t < 28:
        x= math.sin(t)
    return x

def state_machine(z,t):
    u = ext(t)
    x,q,s = z
    dx = u - 0.8*x
    dq = abs(x-u) - 0.8*q
    ds = 0.05*q - 0.04*s
    return [dx,dq,ds]
'''

def dsname():
  return "afreq"

def dsinfo():
  return DSInfo(dsname(), \
                "bias anomaly detector",
                "sensor output",
                "amplitude")

  info.nonlinear = True
  return info


def dsprog(prog):
  params = {
    "charge":0.4,
    "deg":0.8,
    "one":0.99999,
    "X0": 0.0,
    "Q0": 0.0,
    "THRESH0": 0.5
  }
  E = "{one}*X - {one}*U"
  dX = "{one}*U - {deg}*X"
  dQ = "{one}*E*E - {deg}*Q"

  #dTHRESH = "0.05*Q - 0.04*SANE"
  sensor_util.decl_external_input(prog,"U");
  prog.decl_var("E", E, params)
  prog.decl_stvar("X", dX, "{X0}",params)
  prog.decl_stvar("Q", dQ, "{Q0}",params)
  prog.emit("{one}*Q","DETECTOR",params);
  prog.interval("X",0.0,1.0)
  prog.interval("Q",0.0,1.0)

  tau = sensor_util.siggen_time_constant('anomaly-freq')
  prog.speed(tau*0.50,tau*1.25)


def dssim():
  dssim = DSSim('trc');
  prog.interval("X",0.0,1.0)
  prog.interval("THRESH",0.0,1.0)
  dssim.set_sim_time(sensor_util \
                     .siggen_time('anomaly-freq'));
  return dssim;
