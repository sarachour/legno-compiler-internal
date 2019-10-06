from dslang.dsprog import DSProg
from dslang.dssim import DSSim,DSInfo

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
  h = 1.0/N
  tc = 1.0/(2*h)

  nom = 0.9999999
  params = {
    'init_heat': 2.0,
    'one':nom,
    'tc':tc
  }

  for i in range(0,N):
    params["C"] = "D%d" % i
    params["P"] = "D%d" % (i-1) if i-1 >= 0 else None
    params["N"] = "D%d" % (i+1) if i+1 < N else None

    if params['P'] is None:
        dPt = "{tc}*((-{C})+(-{C})+{N})"
    elif params['N'] is None:
        dPt = "{tc}*({P} + (-{C}) + (-{C}) + {init_heat})"
    else:
        dPt = "{tc}*({P} + (-{C}) + (-{C}) + {N})"

    prog.decl_stvar("D%d" % i, dPt, "0.0", params)
    prog.interval("D%d" % i, \
                  0, \
                  params['init_heat'])

  prog.emit("{one}*D%d" % I, "POINT",params)
  prog.check()

def dssim():
  exp = DSSim('t20')
  exp.set_sim_time(20)
  return exp
