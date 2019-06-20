import util.config as CONFIG
from compiler import srcgen
from lab_bench.lib.chipcmd.use import *
import os

PROG = srcgen.GrendelProg()

def log(circ,block_name,loc,config,comp_mode,scale_mode):
  backup_scm = config.scale_mode
  backup_cm = config.comp_mode
  block = circ.board.block(block_name)
  if block.name == 'lut':
    return
  config.set_scale_mode(scale_mode)
  config.set_comp_mode(comp_mode)
  srcgen.gen_block(PROG,circ,block,loc,config)
  config.set_comp_mode(backup_cm)
  config.set_scale_mode(backup_scm)

def is_empty():
  return len(PROG.stmts) == 0
def save():
  minprog = srcgen.GrendelProg()
  stmt_keys = []
  for stmt in PROG.stmts:
    if not isinstance(stmt, UseCommand):
      continue

    if str(stmt) in stmt_keys:
      continue

    minprog.add(stmt)
    stmt_keys.append(str(stmt))
    if os.path.exists(CONFIG.CALIBRATE_FILE):
      mode = 'a' # append if already exists
    else:
      mode = 'w' # make a new file if not

    with open(CONFIG.CALIBRATE_FILE,mode) as fh:
      for stmt in minprog.stmts:
        fh.write("%s\n" % stmt)
