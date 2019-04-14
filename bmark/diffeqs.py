
import bmark.bmarks.spring as spring
import bmark.bmarks.robot_control as robot_control
import bmark.bmarks.oscillator as oscillator
import bmark.bmarks.simple_osc as simple_osc
import bmark.bmarks.repri as repri
import bmark.bmarks.bmmrxn as bmmrxn
import bmark.bmarks.compinh as compinh
import bmark.bmarks.test as test
import bmark.bmarks.rxn as rxn
import bmark.bmarks.vanderpol as vanderpol
import bmark.bmarks.heat as heat
import bmark.bmarks.pendulum as pendulum
import bmark.bmarks.sensor_dynsys as sensor_dynsys
import bmark.bmarks.sensor_fan as sensor_fanout
import bmark.bmarks.bbsys as bbsys

import bmark.bmarks.audio.test as audio_test
import bmark.bmarks.audio.lpf as audio_lpf
import bmark.bmarks.audio.mixer as audio_mixer

# commented out any benchmarks that don't work.
BMARKS = [
    rxn.model_bimolec(),
    rxn.model_dissoc(),
    rxn.model_dimer_mult(),
    #rxn.model_dimer_lut(),
    rxn.model_bidir(),

    simple_osc.model("one",1.0),
    simple_osc.model("quad",4.0),
    simple_osc.model("quarter",0.25, \
                     menv_name='t200'),
    spring.model(),
    oscillator.model(),
    pendulum.model(),
    bmmrxn.model(),
    compinh.model(),
    repri.model(),
    vanderpol.model(),
    heat.model(4,2),
    heat.model(6,2),
    heat.model(8,2),
    heat.model(16,2),
    # external inputs
    #test.model_1(),
    #test.model_1_scale(),
    #test.model_2(),
    #test.model_2_add(),
    #test.model_1_sqrt(),
    #test.model_1_sin(),
    test.zero(),
    robot_control.model(),
    sensor_fanout.model(),
    sensor_dynsys.model(),
    audio_test.model(),
    audio_lpf.model(),
    audio_mixer.model()
]

# energy model: page 26 of thesis, chapter 2
def get_names():
    for _,bmark in BMARKS:
        yield bmark.name

def get_math_env(name):
    for menv,bmark in BMARKS:
        if bmark.name == name:
            return menv

    print("=== available benchmarks ===")
    for _,bmark in BMARKS:
        print("  %s" % bmark.name)
    raise Exception("unknown benchmark: <%s>" % name)

def get_prog(name):
    for _,bmark in BMARKS:
        if bmark.name == name:
            return bmark

    print("=== available benchmarks ===")
    for _,bmark in BMARKS:
        print("  %s" % bmark.name)


    raise Exception("unknown benchmark: <%s>" % name)
