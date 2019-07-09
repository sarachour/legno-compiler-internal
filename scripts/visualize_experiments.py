from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus, MismatchStatus
import scripts.visualize.paper_quality_energy_runtime  \
  as paper_quality_energy_runtime
import scripts.visualize.paper_bmark_summary as paper_bmark_summary
import scripts.visualize.paper_circuit_summary as paper_circuit_summary
import scripts.visualize.paper_chip_summary as paper_chip_summary
import scripts.visualize.paper_compile_time as paper_compile_time
import matplotlib.pyplot as plt
import numpy as np
import math



def execute(args):
  name = args.type
  opts = {
    'paper-quality-energy-runtime': \
    paper_quality_energy_runtime.visualize,
    'paper-chip-summary': paper_chip_summary.visualize,
    'paper-benchmark-summary': paper_bmark_summary.visualize,
    'paper-circuit-summary': paper_circuit_summary.visualize,
    'paper-compile-time': paper_compile_time.visualize,

  }
  if name in opts:
    opts[name]()
  else:
    for opt in opts.keys():
      print(": %s" % opt)
    raise Exception("unknown routine <%s>" % name)
