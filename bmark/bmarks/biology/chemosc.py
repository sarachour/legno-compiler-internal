if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import math
import bmark.menvs as menvs

def model():
  prob = MathProg("chemosc")
  menv = menvs.get_math_env('t200')
  return menv,prob
