import os
import time
import matplotlib.pyplot as plt

from scripts.expdriver_db import ExpDriverDB
from scripts.common import ExecutionStatus
import lab_bench.lib.command as cmd

from chip.conc import ConcCirc

import scripts.analysis.params as params
import scripts.analysis.quality as quality
import scripts.analysis.energy as energy

import tqdm

#board = make_board('standard')

BOARD_CACHE = {}

def execute_once(args,debug=False):
  db = ExpDriverDB()
  entries = list(db.experiment_tbl \
                 .get_by_status(ExecutionStatus.PENDING))


  entries = list(db.experiment_tbl.get_by_status(ExecutionStatus.RAN))
  for entry in tqdm.tqdm(entries):
    if not entry.runtime is None \
      and (not entry.quality is None and not args.recompute_quality)\
      and not entry.energy is None:
      continue


    if not args.bmark is None and not entry.bmark == args.bmark:
      continue

    if not args.subset is None and not entry.subset == args.subset:
      continue

    if not args.model is None and entry.model != args.model:
      continue

    if not args.obj is None and entry.objective_fun != args.obj:
      continue

    board = None
    if not os.path.isfile(entry.jaunt_circ_file):
      continue

    if entry.energy is None or entry.runtime is None or \
       args.recompute_params:
      if not entry.subset in BOARD_CACHE:
        from chip.hcdc.hcdcv2_4 import make_board
        board = make_board(entry.subset)
        BOARD_CACHE[entry.subset] = board
      else:
        board = BOARD_CACHE[entry.subset]
      conc_circ = ConcCirc.read(board,entry.jaunt_circ_file)
      params.analyze(entry,conc_circ)
      energy.analyze(entry,conc_circ)

    if entry.quality is None or args.recompute_quality:
      conc_circ = ConcCirc.read(None,entry.jaunt_circ_file)
      quality.analyze(entry, \
                      recompute=args.recompute_quality,
                      no_reference=(entry.math_env == 'audenv') \
      )

  db.close()

def execute(args,debug=False):
  daemon = args.monitor
  if not daemon:
    execute_once(args,debug=debug)
  else:
    while True:
      execute_once(args,debug=debug)
      print("...")
      time.sleep(10)
