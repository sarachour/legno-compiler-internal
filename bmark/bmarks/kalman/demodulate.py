if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))


from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs




def model():
    prob = MathProg("demod")
    P,V = build_std_bb_sys(prob,ampl,0)

    params {
      'alpha':1.0
    }
    parse_diffeq("{alpha}*(-S)","S0",":x0",params);
    parse_diffeq("S",'THETA0',":x1",params);
