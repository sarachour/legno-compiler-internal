from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
from util.paths import PathHandler
import scripts.img_term as imgterm
import os
import sys
import shutil
import math

def execute(args):
  bmark = args.bmark
  db = ExperimentDB()
  ph = PathHandler('default',bmark)
  siz = shutil.get_terminal_size((80, 20))
  cols = int(siz.columns*0.8)
  rows = int(siz.lines*0.8)
  for entry in db.filter_experiments({'bmark':bmark}):
    mismatched = None
    for outp in entry.get_outputs():
      plotname = ph.plot(outp.bmark,outp.arco_indices,outp.jaunt_index, \
                         outp.objective_fun, \
                         outp.math_env,\
                         outp.hw_env,'%s-meas' % outp.varname)

      if not os.path.isfile(plotname):
        continue

      imgterm.render(plotname,cols,8)
      result = input("mismatch (y/n):")
      if "y" in result:
        mismatched = True
      elif "n" in result:
        mismatched = False

    if not mismatched is None:
      entry.set_mismatch(True)
