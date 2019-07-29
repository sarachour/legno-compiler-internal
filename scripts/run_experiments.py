from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import lab_bench.lib.command as cmd
import lab_bench.lib.expcmd.micro_getter as microget
import lab_bench.lib.expcmd.osc as osc
import os
import time
import util.config as CONFIG

def ping_user(email,entries):
    msg = ""
    with open('body.txt','w') as fh:
        for entry in entries:
            fh.write("%s\n" % entry)

    cmd = "mail -s \" %d jobs finished\" %s  <<< body.txt" \
          % (len(entries),email)

    os.system(cmd)
    os.remove('body.txt')

def execute_script(script_file,calibrate=False):
    print(script_file)
    if not calibrate:
        exec_cmd = "python3 grendel.py %s" % (script_file)
    else:
        exec_cmd = "python3 grendel.py --calibrate %s" % (script_file)

    print(exec_cmd)
    os.system(exec_cmd)
    time.sleep(1)

def execute(args):
  db = ExperimentDB()
  entries = []
  for entry in db.get_by_status(ExperimentStatus.RAN):
    entry.synchronize()

  for entry in db.get_by_status(ExperimentStatus.PENDING):
    entry.synchronize()
    if not args.bmark is None and entry.bmark != args.bmark:
      continue
    if not args.subset is None and entry.subset != args.subset:
      continue

    if not args.model is None and entry.model != args.model:
      continue

    if not args.obj is None and entry.objective_fun != args.obj:
      continue

    if entry.status == ExperimentStatus.PENDING:
        entries.append(entry)


  for entry in entries:
      execute_script(entry.grendel_file, \
                     calibrate=args.calibrate)
      entry.synchronize()

  if not args.email is None:
      ping_user(args.email,entries)
