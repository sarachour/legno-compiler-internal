from lang.prog import MathEnv
def med():
  exp = MathEnv('t20')
  exp.set_sim_time(20)
  exp.set_input_time(10)
  return exp

def med_sin1():
  exp = MathEnv('t20sin1')
  exp.set_sim_time(20)
  exp.set_input_time(10)
  exp.set_input('I','5.0*math.sin(t)')
  return exp

MATH_ENVS = [
  med(),
  med_sin1()
]

def get_math_env(name):
  for exp in MATH_ENVS:
    if exp.name == name:
      return exp

  raise Exception("unknown math_env <%s>" % name)
