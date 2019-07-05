import bmark.bmarks.other.volterra_lotka as lotka
import bmark.bmarks.other.simple_osc as simple_osc
import bmark.bmarks.other.sensor_dynsys as sensor_dynsys
import bmark.bmarks.other.sensor_fan as sensor_fanout
import bmark.bmarks.other.bbsys as bbsys
import bmark.bmarks.other.test as test

def get_benchmarks():
  return [
    simple_osc.model(),
    lotka.model(),
    test.nochange(),
    test.lut(),
    test.feedback(),
    test.feedback2(),
    test.feedback3()
  ]
