import argparse
import os
import sys
from moira.db import ExperimentDB

sys.path.insert(0,os.path.abspath("lab_bench"))

import lab_bench.lib.state as lab_state
import lab_bench.lib.command_handler as lab_handler

# execute script on inputs
def execute(state,model,sim_time):
    for ident,trials,inputs,output in \
        model.db.get_by_status(ExperimentDB.Status.PENDING):

        print(ident,trials,inputs,output)
        outfiles = list(map(lambda trial: \
                            model.db.timeseries_file(ident,trial), trials))

        prog = model.scriptgen.generate(sim_time,inputs,output,outfiles)
        scriptfile = model.db.script_file(ident)
        with open(scriptfile,'w') as fh:
            srccode = "\n".join(prog)
            print(srccode)
            fh.write(srccode)

        input("<run experiment>")
        lab_handler.main_script(state,scriptfile)

        for trial in trials:
            model.db.set_status(ident,trial,ExperimentDB.Status.RAN)
