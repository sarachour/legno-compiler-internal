from dslang.dsprog import DSProg
from dslang.dssim import DSSim
import progs.prog_util as prog_util


def dsname():
  return "template"


def dsprog(prog):
  params = {}
  prog.check()
  return


def dssim():
  exp = DSSim('t20')
  exp.set_sim_time(20)
  return exp
