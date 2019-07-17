import bmark.bmarks.other.volterra_lotka as lotka
import bmark.bmarks.other.simple_osc as simple_osc
import bmark.bmarks.other.sensor_dynsys as sensor_dynsys
import bmark.bmarks.other.sensor_fan as sensor_fanout
import bmark.bmarks.other.bbsys as bbsys
import bmark.bmarks.other.test as test
import bmark.bmarks.other.demo as demo
import bmark.bmarks.other.forced_vanderpol as forced_vanderpol
import bmark.bmarks.other.closed_forced_vanderpol as closed_forced_vanderpol

def get_benchmarks():
  return [
    forced_vanderpol.model(),
    closed_forced_vanderpol.model(),
    simple_osc.model(),
    simple_osc.model_with_gain(),
    demo.legno_demo(),
    lotka.model(),
    test.nochange(),
    test.integrate_noise(),
    test.lut(),
    test.feedback(),
    test.feedback2(),
    test.feedback3()
  ]
