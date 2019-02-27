from scripts.db import ExperimentDB, ExperimentStatus, OutputStatus
import lab_bench.lib.command as cmd
import lab_bench.lib.expcmd.micro_getter as microget
import lab_bench.lib.expcmd.osc as osc
import os
import time

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

def detect_executed(entry):
  for output in entry.outputs():
    if os.path.isfile(output.out_file)  \
       and output.status == OutputStatus.PENDING:
      output.set_status(OutputStatus.RAN)


  not_done = any(map(lambda out: out.status == OutputStatus.PENDING, \
                     entry.outputs()))
  if not not_done:
    entry.set_status(ExperimentStatus.RAN)
  return not not_done

db = ExperimentDB()
db.scan()
ip = "128.30.70.218"
native = False
for entry in db.get_by_status(ExperimentStatus.PENDING):
  print(entry)
  if not detect_executed(entry):
    execute_script(ip,entry.grendel_file,native=native)

  detect_executed(entry)
