
import bmark.bmarks.spring as spring
import bmark.bmarks.robot_control as robot_control
import bmark.bmarks.oscillator as oscillator
import bmark.bmarks.simple_osc as simple_osc
import bmark.bmarks.repri as repri
import bmark.bmarks.bmmrxn as bmmrxn
import bmark.bmarks.bmmrxn as gentoggle
import bmark.bmarks.inout as inout
import bmark.bmarks.vanderpol as vanderpol
import bmark.bmarks.heat as heat
import bmark.bmarks.pendulum as pendulum

BMARKS = [
    inout.model0(),
    inout.model1(),
    inout.model2(),
    inout.model3(),
    simple_osc.model("one",1.0),
    simple_osc.model("quad",4.0),
    simple_osc.model("quarter",0.25),
    spring.model(),
    oscillator.model(),
    pendulum.model(),
    robot_control.model(),
    repri.model(),
    vanderpol.model(),
    heat.model(4),
    heat.model(8),
    heat.model(16)
]

# energy model: page 26 of thesis, chapter 2

def get_math_env(name):
    for menv,bmark in BMARKS:
        if bmark.name == name:
            return menv

    raise Exception("unknown benchmark: <%s>" % name)

def get_prog(name):
    for _,bmark in BMARKS:
        if bmark.name == name:
            return bmark

    raise Exception("unknown benchmark: <%s>" % name)
