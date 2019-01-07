from lang.prog import MathEnv
def med_time():
  exp = MathEnv('t20')
  exp.set_sim_time(20)
  exp.set_input_time(20)
  return exp

def medlong_time():
  exp = MathEnv('t200')
  exp.set_sim_time(200)
  exp.set_input_time(200)
  return exp


def long_time():
  exp = MathEnv('t2k')
  exp.set_sim_time(2000)
  exp.set_input_time(2000)
  return exp


def long_sin1():
  exp = MathEnv('t2ksin1')
  exp.set_sim_time(2000)
  exp.set_input_time(2000)
  exp.set_input('I','5.0*math.sin(0.01*t)')
  return exp


def long_sin2():
  exp = MathEnv('t2ksin2')
  exp.set_sim_time(2000)
  exp.set_input_time(2000)
  exp.set_input('I2','5.0*math.sin(0.01*t)')
  exp.set_input('I1',\
      '3.0*math.sin(0.01*t)+2.0*math.cos(0.037*t)')
  return exp

MATH_ENVS = [
  med_time(),
  long_time(),
  medlong_time(),
  long_sin1(),
  long_sin2()
]

def get_math_env(name):
  for exp in MATH_ENVS:
    if exp.name == name:
      return exp

  raise Exception("unknown math_env <%s>" % name)
