from scripts.expdriver_db import ExpDriverDB
from scripts.common import ExecutionStatus
import lab_bench.lib.command as cmd
import lab_bench.lib.expcmd.micro_getter as microget
import lab_bench.lib.expcmd.osc as osc
import os
import time
import util.config as CONFIG
import util.util as util

def ping_user(email,entries):
    msg = ""
    with open('body.txt','w') as fh:
        for entry in entries:
            fh.write("%s\n" % entry)

    cmd = "mail -s \" %d jobs finished\" %s  <<< body.txt" \
          % (len(entries),email)

    os.system(cmd)
    os.remove('body.txt')

def execute_script(script_file, \
                   calib_obj, \
                   calibrate=False):
    print(script_file)
    if not calibrate:
        calib_cmd = "python3 grendel.py --calib-obj {obj} calibrate {script}"
        cmd = calib_cmd.format(obj=calib_obj, \
                               script=script_file)
        os.system(cmd)

    exec_cmd = "python3 grendel.py --calib-obj {obj} run {script}"
    cmd = exec_cmd.format(obj=calib_obj, \
                           script=script_file)
    os.system(cmd)

def execute(args):
    from compiler.jaunt_pass.jenv import JauntEnvParams
    db = ExpDriverDB()
    entries = []
    for entry in db.experiment_tbl.get_by_status(ExecutionStatus.RAN):
        print(entry)
        entry.synchronize()

    for entry in db.experiment_tbl.get_by_status(ExecutionStatus.PENDING):
        entry.synchronize()

        if not args.bmark is None and entry.bmark != args.bmark:
            continue
        if not args.subset is None and entry.subset != args.subset:
            continue

        if not args.model is None and entry.model != args.model:
            continue

        if not args.obj is None and entry.objective_fun != args.obj:
            continue

        if entry.status == ExecutionStatus.PENDING:
            entries.append(entry)


    for entry in entries:
        method,mape,mdpe,bw = util.unpack_tag(entry.model)
        pars = JauntEnvParams(digital_error=mdpe, \
                              analog_error=mape,
                              max_freq=bw)
        pars.set_model(JauntEnvParams.Type(method))
        execute_script(entry.grendel_file, \
                       calib_obj=pars.calib_obj, \
                       calibrate=args.calibrate)
        entry.synchronize()

    if not args.email is None:
        ping_user(args.email,entries)
