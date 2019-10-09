from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.sensor.sensor_util as sensor_util
import hwlib.units as units

def dsname():
  return "apower"

def dsinfo():
  return DSInfo(dsname(), \
                "power anomaly detector",
                "anomaly detected",
                "amplitude")
  info.nonlinear = True
  return info

'''
def ext(t):
    x =  math.sin(t)
    if t > 20 and t < 28:
        return math.sin(t)
    return x
def state_machine(z,t):
    u = ext(t)
    x,s,a = z
    dx = 0.4*u*u - 0.1*x
    ds = 0.1*x - 0.08*s
    da = s-x if a < 2.0 else 0
    return [dx,ds,da]
'''

def dsprog(prog):
  params = {
    "charge":0.4,
    "deg":0.1,
    "tcharge":0.1,
    "tdeg": 0.05,
    "SANE0":1.0,
    "one":0.99999
  }

  dX = "{charge}*U*U - {deg}*X"
  dTHRESH = "{tcharge}*X - {tdeg}*THRESH"
  dSANE = "THRESH+(-X)"
  sensor_util.decl_external_input(prog,"U");
  prog.decl_stvar("X",dX,"0.0",params)
  prog.decl_stvar("THRESH",dTHRESH,"0.0",params)
  #prog.decl_stvar("SANE",dSANE,"1.0",params)
  '''
  TODO: debug threshold, end goal is to have sane trigger work.
  '''
  prog.interval("X",0.0,5.0)
  prog.interval("THRESH",0.0,5.0)
  #prog.interval("SANE",0.0,2.0)
  prog.emit("{one}*THRESH","DETECTOR",params);
  tau = sensor_util.siggen_time_constant('anomaly-ampl')
  prog.speed(tau*0.50,tau*1.25)


def dssim():
  dssim = DSSim('trc');
  dssim.set_sim_time(sensor_util \
                     .siggen_time('anomaly-ampl'));
  return dssim;
