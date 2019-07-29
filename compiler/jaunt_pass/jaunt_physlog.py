import util.config as CONFIG
from compiler import srcgen
from lab_bench.lib.chipcmd.use import *
import lab_bench.lib.command as cmd

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
  if scale_mode is None:
    return

  srcgen.gen_block(PROG,circ,block,loc,config)
  config.set_comp_mode(backup_cm)
  config.set_scale_mode(backup_scm)

def is_empty():
  return len(PROG.stmts) == 0

def clear():
  PROG.clear()

def save():
  minprog = srcgen.GrendelProg()
  stmt_keys = []
  if os.path.isfile(CONFIG.CALIBRATE_FILE):
    with open(CONFIG.CALIBRATE_FILE,'r') as fh:
      for line in fh:
        stmt = cmd.parse(line)
        stmt_keys.append(str(stmt))

  for stmt in PROG.stmts:
    if not isinstance(stmt, UseCommand):
      continue

    if str(stmt) in stmt_keys:
      continue

    minprog.add(stmt)
    stmt_keys.append(str(stmt))


  if os.path.exists(CONFIG.CALIBRATE_FILE):
    lines = []
    with open(CONFIG.CALIBRATE_FILE,'r') as fh:
      for line in fh:
        lines.append(line.strip())
  else:
    lines = []

  print("JAUNTLOG: logged %d stmts" % len(minprog.stmts))
  with open(CONFIG.CALIBRATE_FILE,'w') as fh:
    for line in lines:
      fh.write("%s\n" % line)

    for stmt in minprog.stmts:
      stmt_str = str(stmt)
      if not stmt_str in lines:
        fh.write("%s\n" % stmt)
        lines.append(stmt_str)
