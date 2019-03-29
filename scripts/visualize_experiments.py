from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus, MismatchStatus
import scripts.visualize.correlation as correlation
import scripts.visualize.scalecorr as scale_analysis
import scripts.visualize.paper_quality_vs_speed as paper_quality_vs_speed
import scripts.visualize.paper_quality_vs_energy as paper_quality_vs_energy
import scripts.visualize.paper_quality_vs_runtime as paper_quality_vs_runtime
import scripts.visualize.quality_vs_speed as quality_vs_speed
import scripts.visualize.quality_vs_energy as quality_vs_energy
import scripts.visualize.rank_vs_speed as rank_vs_speed
import scripts.visualize.best_of as best_of
import scripts.visualize.component_count as component_count
import scripts.visualize.bmark_summary as bmark_summary
import matplotlib.pyplot as plt
import numpy as np
import math



def execute(args):
  name = args.type
  opts = {
    'quality-vs-speed':quality_vs_speed.visualize,
    'quality-vs-energy':quality_vs_energy.visualize,
    'rank-vs-speed':rank_vs_speed.visualize,
    'correlation': correlation.visualize,
    'scale-analysis': scale_analysis.visualize,
    'best-rank': best_of.rank,
    'best-quality': best_of.quality,
    'best-quality-to-speed': best_of.quality_to_speed,
    'best-quality-variance': best_of.quality_variance,
    'best-speed': best_of.speed,
    'paper-qvs': paper_quality_vs_speed.visualize,
    'paper-qve': paper_quality_vs_energy.visualize,
    'paper-qvr': paper_quality_vs_runtime.visualize,
    'component-summary': component_count.visualize,
    'benchmark-summary': bmark_summary.visualize

  }
  if name in opts:
    opts[name]()
  else:
    for opt in opts.keys():
      print(": %s" % opt)
    raise Exception("unknown routine <%s>" % name)
