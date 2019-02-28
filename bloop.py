from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import matplotlib.pyplot as plt
import numpy as np
import math

db = ExperimentDB()
bmarks = ['micro-osc-quarter','micro-osc-quad','micro-osc-one', \
          'spring','vanderpol','pend','cosc']
opts = ['fast','slow','max','maxstab']
series = opts
qualities = dict(map(lambda opt: (opt,[]), series))
ranks = dict(map(lambda opt: (opt,[]), series))
times = dict(map(lambda opt: (opt,[]), series))
best_quality = dict(map(lambda opt: (opt,{}), bmarks))


all_times = []
all_snrs = []
for entry in db.get_all():
  if not entry.bmark in bmarks:
    continue

  if not entry.quality is None and \
     not entry.runtime is None and \
     not entry.rank is None:
    print(str(entry).split('\n')[1])
    bmark = entry.bmark
    opt = entry.objective_fun
    ser = opt
    ranks[ser].append(entry.rank)
    qualities[ser].append(entry.quality)
    times[ser].append(math.log(entry.runtime))
    best_quality[bmark][opt] = entry.quality

for bmark in bmarks:
  if len(best_quality[bmark]) == 0:
    continue

  res = max(list(best_quality[bmark].items()),key=lambda a: a[1])
  print("%s: %s" % (bmark,str(res)))
  print("  %s" % str(best_quality[bmark]))

for ser in series:
  coeff = np.corrcoef(ranks[ser],qualities[ser])
  print("[%s] correlation:\n%s" % (ser,coeff))
  plt.scatter(ranks[ser],qualities[ser],label=ser)

plt.legend()
plt.savefig("rank.png")
plt.clf()
for ser in series:
  plt.scatter(times[ser], qualities[ser],label=ser,s=1.0)

plt.legend()
plt.savefig("runt.png")
plt.clf()
 
