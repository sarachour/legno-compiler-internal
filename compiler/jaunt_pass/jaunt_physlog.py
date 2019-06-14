import util.config as CONFIG
from compiler import srcgen
from lab_bench.lib.chipcmd.use import *

PROG = srcgen.GrendelProg()

def log(circ,block,loc,config,scale_mode):
  backup_scm = config.scale_mode
  config.set_scale_mode(scale_mode)
  srcgen.gen_block(PROG,circ,block,loc,config)
  config.set_scale_mode(backup_scm)

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

  minprog.write(CONFIG.CALIBRATE_FILE)
