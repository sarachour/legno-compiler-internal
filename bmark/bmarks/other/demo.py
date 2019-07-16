
def legno_demo():
  # system parameters
  params = {
    'Y0':0.1,
    'Z':0.2
  }
  # create a new math program named demo
  prob = MathProg("demo")
  Y = parse_diffeq('{Z}+(-Y)', 'Y0', ':a', params)
  
  # bind the differential equation to the variable Y. 
  prob.bind("Y",Y)
  # measure Y, name the measurement O
  prob.bind("O",op.Emit(op.Var('Y'),loc='A0'))
  prob.set_interval("Y",-1.0,1.0)
  
  # compile benchmark
  prob.compile()
  
  menv = menvs.get_math_env('t20')
  prob.set_max_sim_time(20)
  
  return menv,prob
