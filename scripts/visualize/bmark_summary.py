import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt
import bmark.diffeqs as diffeq
from enum import Enum
import ops.op as op

DESCRIPTIONS = {
  'micro-osc-quarter': 'differential equation representation of sin function',
  'pend': 'pendulum simulation with no small angle estimation',
  'spring': 'simulation of two boxes connected with springs',
  'vanderpol': 'stiff vanderpol oscillator',
  'sensor-dynsys': 'linear parameter estimation between $x(t)$ and $y(t) ~ x(t)^2$',
  'sensor-fanout': 'linear parameter estimation between $x(t)$ and $y(t)~x(t)$',
  'cosc': 'dampened spring physics simulation',
  'heat1d-g8': 'movement of heat through lattice'

}
OBSERVATIONS = {
  'micro-osc-quarter': '',
  'pend': 'position',
  'spring': 'position of block 1',
  'vanderpol': '',
  'sensor-dynsys': 'parameter A',
  'sensor-fanout': 'parameter A',
  'cosc': 'position',
  'heat1d-g8': 'heat at point XXX'
}
NONLINEAR = {
  'micro-osc-quarter': False,
  'pend': True,
  'heat1d-g8': False,
  'spring': True,
  'vanderpol': True,
  'sensor-dynsys': True,
  'sensor-fanout': True,
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
  for bmark in table.benchmarks:
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
      'description': DESCRIPTIONS[bmark],
      'observation': OBSERVATIONS[bmark],
      'diffeqs': n_diffeqs,
      'funcs': n_funcs,
      'time': str(menv.sim_time) + " su",
      'nonlinear': bool_to_field[NONLINEAR[bmark]]
    }
    table.data(bmark,entry)

  table.write('bmarksummary.tbl')
