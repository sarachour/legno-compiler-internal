from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import matplotlib.pyplot as plt
import numpy as np

db = ExperimentDB()
bmarks = ['micro-osc-quarter','micro-osc-quad','micro-osc-one', \
          'spring']

qualities = dict(map(lambda bmark: (bmark,[]), bmarks))
ranks = dict(map(lambda bmark: (bmark,[]), bmarks))
for entry in db.get_all():
  if not entry.bmark in bmarks:
    continue

  if not entry.quality is None and \
     not entry.runtime is None and \
     not entry.rank is None:
    print(str(entry).split('\n')[1])
    bmark = entry.bmark()
    ranks[bmark].append(entry.rank)
    qualities[bmark].append(entry.quality)

for bmark in bmarks:
  coeff = np.corrcoef(ranks[bmark],qualities[bmark])
  print("rank/quality correlation:\n%s" % coeff)
