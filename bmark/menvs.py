from lang.prog import MathEnv
import ops.op as op


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

def long_sin0():
  exp = MathEnv('t2ksin0')
  expr = op.Sin(op.Mult(op.Const(0.01), op.Var('t')))
  exp.set_sim_time(2000)
  exp.set_input_time(2000)
  exp.set_input('I',expr)
  return exp



def long_sin1():
  expr = op.Mult(op.Const(5.0), \
                 op.Sin(op.Mult(op.Const(0.01), op.Var('t'))))
  exp = MathEnv('t2ksin1')
  exp.set_sim_time(2000)
  exp.set_input_time(2000)
  exp.set_input('I',expr)
  return exp


def long_sin2():
  expr1 = op.Mult(op.Const(5.0), \
                 op.Sin(op.Mult(op.Const(0.01), op.Var('t'))))
  expr2 = op.Add(
    op.Mult(op.Const(0.2), \
            op.Sin(op.Mult(op.Const(0.037), op.Var('t')))),
    op.Mult(op.Const(0.1), \
            op.Sin(op.Mult(op.Const(0.01), op.Var('t'))))
  )

  exp = MathEnv('t2ksin2')
  exp.set_sim_time(2000)
  exp.set_input_time(2000)
  exp.set_input('I2',expr1)
  exp.set_input('I1',expr2)
  return exp

MATH_ENVS = [
  short_time(),
  med_time(),
  long_time(),
  medlong_time(),
  long_sin0(),
  long_sin1(),
  long_sin2()
]

def get_math_env(name):
  for exp in MATH_ENVS:
    if exp.name == name:
      return exp

  raise Exception("unknown math_env <%s>" % name)
