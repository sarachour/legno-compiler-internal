import argparse
import os
import sys
from moira.db import ExperimentDB

sys.path.insert(0,os.path.abspath("lab_bench"))

import lab_bench.lib.state as lab_state
import lab_bench.lib.command_handler as lab_handler


dac_setup_message = """
DAC Experiment Setup Instructions:
1. Make sure you set voltage threshhold for the clock to 100mV
2. Clip the EXT signal probe to the SDA port and the ground probe to Arduino GND
3. Clip the CH1 signal probe to DAC0/1 and the ground probe to Arduino ground
"""

vdiv_setup_message = """
VDiv circuit Setup Instructions:
0. When the chip is off, connect breadboard voltage to 3.3V voltage source from Arduino Due, and the ground lead to the GND pin in the Arduino Due.
1. Make sure you set voltage threshhold for the clock to 100mV
2. Clip the EXT signal probe to the SDA port and the ground probe to Arduino GND
3. Clip the CH1 signal probe to the purple wire on the breadboard and the ground probe to breadboard  GND. (left pair for VDIV0, right pair for VDIV1)
4. Clip the CH2 signal probe to the gray wire on the breadboard and the ground probe to breadboard  GND.
"""
def emit_prompt(model):
    if 'vdiv' in model.name:
        print(vdiv_setup_message)
        input("<i'm ready!>")

    elif 'due_dac' in model.name:
        print(dac_setup_message)
        input("<i'm ready!>")

# execute script on inputs
def execute(state,model,sim_time):
    initialized = False
    for ident,trials,inputs,output in \
        model.db.get_by_status(ExperimentDB.Status.PENDING):
        if not initialized:
            emit_prompt(model)
            state.initialize()
            initialized = True

        print(ident,trials,inputs,output)
        outfiles = list(map(lambda trial: \
                            model.db.timeseries_file(ident,trial), trials))

        prog = model.scriptgen.generate(sim_time,inputs,output,outfiles)
        scriptfile = model.db.script_file(ident)
        with open(scriptfile,'w') as fh:
            srccode = "\n".join(prog)
            print(srccode)
            fh.write(srccode)

        #input("<run experiment>")
        #lab_handler.main_script(state,scriptfile)

        for trial in trials:
            model.db.set_status(ident,trial,ExperimentDB.Status.RAN)

    if initialized:
        state.close()
