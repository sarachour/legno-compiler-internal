from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus, MismatchStatus
import scripts.visualize.correlation as correlation
import scripts.visualize.quality_vs_speed as quality_vs_speed
import scripts.visualize.rank_vs_speed as rank_vs_speed
import scripts.visualize.best_of as best_of
import matplotlib.pyplot as plt
import numpy as np
import math



def execute(args):
  name = args.type
  opts = {
    'quality-vs-speed':quality_vs_speed.visualize,
    'rank-vs-speed':rank_vs_speed.visualize,
    'correlation': correlation.visualize,
    'best-rank': best_of.rank,
    'best-quality': best_of.quality,
    'best-quality-to-speed': best_of.quality_to_speed,
    'best-speed': best_of.speed
  }
  if name in opts:
    opts[name]()
  else:
    for opt in opts.keys():
      print(": %s" % opt)
    raise Exception("unknown routine <%s>" % name)
