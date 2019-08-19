import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt
import bmark.diffeqs as diffeq
from enum import Enum
import ops.op as op

DESCRIPTIONS = {
  'micro-osc': 'differential equation representation of sin function',
  'pend': 'pendulum simulation.$\dagger$',
  'pend-nl': 'pendulum simulation.$\dagger$',
  'spring': 'simulation of box-spring system.$\dagger$',
  'spring-nl': 'simulation of box-spring system.$\dagger$',
  'vanderpol': 'stiff vanderpol oscillator',
  'cosc': 'dampened spring physics simulation',
  'heat1d': 'movement of heat through lattice',
  'robot': 'PID control system',
  'gentoggle': 'genetic toggle switch',
  'kalman-const': 'kalman filter',
  'smmrxn': 'michaelis menten reaction',
  'bont': 'botulism neurotoxin model (reparametrized)',
  'repri': 'reprissilator (reparametrized)',
  'gentoggle': 'genetic toggle switch',
  'closed-forced-vanderpol':'chaotic vanderpol oscillator'

}
OBSERVATIONS = {
  'micro-osc': '',
  'pend-nl': 'position of pendulum',
  'spring': 'position of block 1',
  'spring-nl': 'position of block 1',
  'vanderpol': '',
  'closed-forced-vanderpol': '',
  'cosc': '',
  'robot': 'velocity of left wheel',
  'repri': 'chemical compounds',
  'heat1d': 'heat at point',
  'gentoggle': 'concentration of protein',
  'repri': 'concentration of protein',
  'bont': 'concentration of protein',
  'smmrxn': 'concentration of protein',
  'kalman-const': 'state estimation'
}
NONLINEAR = {
  'micro-osc': False,
  'pend': True,
  'pend-nl': True,
  'robot': False,
  'heat1d': False,
  'spring': True,
  'spring-nl': True,
  'vanderpol': True,
  'closed-forced-vanderpol': True,
  'gentoggle': True,
  'kalman-const': True,
  'cosc': False,
  'bont': True,
  'smmrxn': True
}
def visualize():
  header = ['description', 'observation','time','diffeqs','funcs','nonlinear']
  desc = 'dynamical system benchmarks used in evaluation. $\dagger$ these benchmarks '
  table = common.Table('Benchmarks',desc, 'bmarksumm', '|c|lccccc|')
  table.two_column = True
  bool_to_field = {True:'yes',False:'no'}
  table.set_fields(header)
  table.horiz_rule()
  table.header()
  table.horiz_rule()
  for bmark in table.benchmarks():
    bmark_name = bmark
    if 'heat1d' in bmark:
      bmark_name = 'heat1d'

    prog = diffeq.get_prog(bmark)
    menv = diffeq.get_math_env(bmark)
    n_diffeqs = 0
    n_funcs = 0
    for v,bnd in prog.bindings():
      if bnd.op == op.OpType.INTEG:
        n_diffeqs += 1
      else:
        n_funcs += 1

    entry = {
      'description': DESCRIPTIONS[bmark_name],
      'observation': OBSERVATIONS[bmark_name],
      'diffeqs': n_diffeqs,
      'funcs': n_funcs,
      'time': str(menv.sim_time) + " su",
      'nonlinear': bool_to_field[NONLINEAR[bmark_name]]
    }
    table.data(bmark,entry)
  table.horiz_rule()

  table.write(common.get_path('bmarks.tbl'))
