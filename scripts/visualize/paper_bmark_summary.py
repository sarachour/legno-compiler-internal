import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt
import bmark.diffeqs as diffeq
from enum import Enum
import ops.op as op

DESCRIPTIONS = {
  'micro-osc': 'differential equation representation of sin function',
  'pend': 'pendulum simulation with no small angle estimation.$cross$',
  'spring': 'simulation of two boxes connected with springs.$cross$',
  'vanderpol': 'stiff vanderpol oscillator',
  'cosc': 'dampened spring physics simulation',
  'heat1d': 'movement of heat through lattice',
  'robot': 'robotics control system'

}
OBSERVATIONS = {
  'micro-osc': '',
  'pend': 'position of pendulum',
  'spring': 'position of block 1',
  'vanderpol': '',
  'cosc': '',
  'robot': 'velocity of left wheel',
  'repri': 'chemical compounds',
  'heat1d': 'heat at point'
}
NONLINEAR = {
  'micro-osc': False,
  'pend': True,
  'robot': True,
  'heat1d': False,
  'spring': True,
  'vanderpol': True,
  'cosc': False
}
def visualize():
  header = ['description', 'observation','time','diffeqs','funcs','nonlinear']
  desc = 'dynamical system benchmarks used in evaluation'
  table = common.Table('Benchmarks',desc, 'bmarksumm', 'c|lccccc')
  bool_to_field = {True:'yes',False:'no'}
  table.set_fields(header)
  table.horiz_rule()
  table.header()
  table.horiz_rule()
  for bmark in table.benchmarks():
    if bmark == 'pend-nl' or bmark == 'spring-nl':
      continue

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

  table.write('bmarks.tbl')
