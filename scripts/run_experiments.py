from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import lab_bench.lib.command as cmd
import lab_bench.lib.expcmd.micro_getter as microget
import lab_bench.lib.expcmd.osc as osc
import os
import time
import util.config as CONFIG

def chunks(l, n):
    # For item i in a range that is a length of l,
    for i in range(0, len(l), n):
        # Create an index range for l of n items:
        yield l[i:i+n]

def ping_user(email,benchmark,script_list):
    msg = "benchmark=%s"
    cmd = "mail -s \"job finished\" %s  <<< \"%s\"" % (email, msg)
    os.system(cmd)

def execute_script(ip,script_file,native=False):
    print(script_file)
    if not ip is None:
        exec_cmd = "python3 grendel.py --ip %s --script %s" % (ip,script_file)
        exec_cmd += " --native" if native else ""
    else:
        exec_cmd = "python3 grendel.py --script %s" % (script_file)
        exec_cmd += " --native" if native else ""

    print(exec_cmd)
    os.system(exec_cmd)
    time.sleep(1)

def execute(args,batch_size=5):
  db = ExperimentDB()
  ip = args.ip
  if args.ip is None:
      ip = CONFIG.OSC_IP
  native = args.native
  entries = []
  for entry in db.get_by_status(ExperimentStatus.PENDING):
    entry.synchronize()
    if not args.bmark is None and entry.bmark != args.bmark:
      continue

    if not args.obj is None and entry.objective_fun != args.obj:
      continue

    if entry.status == ExperimentStatus.PENDING:
        entries.append(entry)


  for chunk in chunks(entries,batch_size):
      prog = ""
      for entry in chunk:
          snippet = open(entry.grendel_file, 'r').read()
          prog += snippet

      with open('batch.grendel','w') as fh:
          fh.write(prog)

      execute_script(ip,'batch.grendel',native=native)

      for entry in chunk:
          entry.synchronize()
