from bmark.bmarks.other import volterra_lotka,\
        simple_osc,sensor_dynsys,sensor_fan,\
        bbsys,test,demo,forced_vanderpol,\
                closed_forced_vanderpol

def get_benchmarks():
  return [
    forced_vanderpol.model(),
    closed_forced_vanderpol.model(),
    simple_osc.model(),
    simple_osc.model_with_gain(),
    demo.legno_demo(),
    volterra_lotka.model(),
    test.nochange(),
    test.integrate_noise(),
    test.lut(),
    test.constant(),
    test.feedback(),
    test.feedback2(),
    test.feedback3()
  ]
