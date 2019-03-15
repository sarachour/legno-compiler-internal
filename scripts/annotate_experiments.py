from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus, MismatchStatus
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
    mismatch = None
    if not entry.mismatch == MismatchStatus.UNKNOWN and not args.recompute:
      continue
    for outp in entry.get_outputs():
      plotname = ph.plot(outp.bmark,outp.arco_indices,outp.jaunt_index, \
                         outp.objective_fun, \
                         outp.math_env,\
                         outp.hw_env,'%s-meas' % outp.varname)

      if not os.path.isfile(plotname):
        continue

      imgterm.render(plotname,cols,8)
      print("<status=%s>" % entry.mismatch)
      opts = ",".join(MismatchStatus.abbrevs())
      statusline = "status (%s):" % opts
      result = input(statusline)
      if result == "":
        continue
      mismatch= MismatchStatus.from_abbrev(result)
      print(mismatch)

    if not mismatch is None:
      entry.set_mismatch(mismatch)
