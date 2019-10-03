from dslang.dsprog import DSProg
from dslang.dssim import DSSim

N = 4
I = 3
WITH_GAIN = False


def dsname():
  return "heat1dwg"

def dsinfo():
  return DSInfo(dsname(), \
                "heat1d",
                "signal",
                "signal")
  info.nonlinear = True
  return info


def dsprog(prog):
  params = {
    'init_heat': 2.0,
    'one':0.99999
  }

  for i in range(0,N):
    params["C"] = "D%d" % i
    params["P"] = "D%d" % (i-1) if i-1 >= 0 else None
    params["N"] = "D%d" % (i+1) if i+1 < N else None

    if params['P'] is None:
        dPt = "2.0*(-{C}) + {one}*{N}"
    elif params['N'] is None:
        dPt = "{P} + 2.0*(-{C}) + {init_heat}"
    else:
        dPt = "{P} + 2.0*(-{C}) + {one}*{N}"

    prog.decl_stvar("D%d" % i, dPt, "0.0", params)
    prog.interval("D%d" % i, \
                  0, \
                  params['init_heat']*2.0)

  prog.emit("{one}*D%d" % I, "POINT",params)
  prog.check()

def dssim():
  exp = DSSim('t200')
  exp.set_sim_time(200)
  return exp
