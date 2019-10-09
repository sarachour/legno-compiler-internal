from dslang.dsprog import DSProg
from dslang.dssim import DSSim, DSInfo
import progs.sensor.sensor_util as sensor_util


def dsname():
  return "aheart"

def dsinfo():
  return DSInfo(dsname(), \
                "heartbeat model",
                "sensor output",
                "amplitude")
  info.nonlinear = True
  return info

# zeeman heart model with external pacemaker
def dsprog(prog):
  params = {"one":0.999999, \
            "eps":0.2, \
            "T": 1.0, \
            "xd": 1.024, \
            "xs": 0.0, \
            "X0": 1.0, \
            "B0": 0.0
  }
  sensor_util.decl_external_input(prog,"U");
  params['ieps'] = 1.0*params['eps']
  params['nieps'] = -params['ieps']
  params['xds'] = params['xd'] - params['xs']
  params['nxds'] = -params['xds']
  dX = "{ieps}*X3 + {T}*{ieps}*X  + {nieps}*(B)"
  dB = "{ieps}*X + {nxds}*(U)"
  prog.decl_var("X3", "(X*X)*(-X)")
  prog.decl_stvar("X", dX, "{X0}", params);
  prog.decl_stvar("B", dB, "{B0}", params);
  prog.emit("{one}*X","HEARTBEAT",params);
  tc = sensor_util.siggen_time_constant('heart-normal');
  prog.speed(0.75*tc,tc*1.25)
  prog.interval("X",-2.0,2.0)
  prog.interval("B",-2.0,2.0)


def dssim():
  dssim = DSSim('trc');
  dssim.set_sim_time(sensor_util \
                     .siggen_time('heart-normal'));
  return dssim;
