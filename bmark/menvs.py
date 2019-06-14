from lang.prog import MathEnv
import ops.op as op

def audio():
  exp = MathEnv('audio');
  exp.set_sim_time(2)
  exp.set_input_time(2)
  return exp

def short_time():
  exp = MathEnv('t2')
  exp.set_sim_time(2)
  exp.set_input_time(2)
  return exp


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


def sensor_env_steady():
  exp = MathEnv('sensteady')
  sense = op.Mult(op.Const(0.1), \
                  op.Abs(
                    op.Sin(op.Mult(op.Const(0.1),op.Var('t')))
                  )
    )
  motor = op.Mult(op.Const(0.5), \
                  op.Sin(op.Mult(op.Const(0.1),op.Var('t'))))

  exp.set_sim_time(1000)
  exp.set_input_time(1000)
  exp.set_input('MOTOR',motor)
  exp.set_input('SENSE',sense)
  return exp


MATH_ENVS = [
  short_time(),
  med_time(),
  audio(),
  long_time(),
  medlong_time(),
  long_time()
]

def get_math_env(name):
  for exp in MATH_ENVS:
    if exp.name == name:
      return exp

  raise Exception("unknown math_env <%s>" % name)
