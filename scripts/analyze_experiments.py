import os
import time
import matplotlib.pyplot as plt

from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import lab_bench.lib.command as cmd
import lab_bench.lib.expcmd.micro_getter as microget
import lab_bench.lib.expcmd.osc as osc

from chip.conc import ConcCirc
from chip.hcdc.hcdcv2_4 import board as hdacv2_board

import compiler.skelter as skelter


import scripts.analysis.params as params
import scripts.analysis.quality as quality
import scripts.analysis.energy as energy

def missing_params(entry):
  return entry.rank is None or \
    entry.runtime is None

def execute_once(args):
  recompute_params = args.recompute_params
  recompute_quality = args.recompute_quality
  recompute_energy = args.recompute_energy
  recompute_any = recompute_params or  \
                  recompute_quality or \
                  recompute_energy

  db = ExperimentDB()
  for entry in db.get_by_status(ExperimentStatus.PENDING):
    if not missing_params(entry) is None and not recompute_params:
      continue

    print(entry)
    conc_circ = ConcCirc.read(hdacv2_board,entry.skelt_circ_file)
    params.analyze(entry,conc_circ)

  for entry in db.get_by_status(ExperimentStatus.RAN):
    if not entry.runtime is None \
      and not entry.quality is None \
      and not missing_params(entry) \
      and not entry.energy is None \
      and not recompute_any:
      continue

    print(entry)

    if missing_params(entry) or recompute_params:
      conc_circ = ConcCirc.read(hdacv2_board,entry.skelt_circ_file)
      params.analyze(entry,conc_circ)

    if entry.energy is None or recompute_energy:
      conc_circ = ConcCirc.read(hdacv2_board,entry.skelt_circ_file)
      energy.analyze(entry,conc_circ)

    if entry.quality is None or recompute_quality:
      quality.analyze(entry)

def execute(args):
  daemon = args.monitor
  if not daemon:
    execute_once(args)
  else:
    while True:
      execute_once(args)
      print("...")
      time.sleep(10)
