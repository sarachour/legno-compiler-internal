from ops import op, opparse
from scipy.integrate import ode
import matplotlib.pyplot as plt
import numpy as np
import math
import os
import tqdm

def parse_fn(expr,params):
    expr_conc = expr.format(**params)
    print(expr_conc)
    return opparse.parse(expr_conc)


def parse_diffeq(expr,ic, handle,params):
    deriv = opparse.parse(expr.format(**params))
    const = params[ic]
    return op.Integ(deriv,op.Const(const),handle=handle)

def run_fxn(menv,prob):
  time = menv.sim_time
  n = 100.0*menv.sim_time
  dt = time/n
  T = np.linspace(0.0,menv.sim_time,n)
  Z = []
  for t in T:
    z = prob.curr_state(menv,t,[])
    Z.append(z)

  return T,Z


def plot_fxn(menv,prob,T,Z):
  cwd = os.getcwd()
  filedir = "%s/BMARK_REF/%s_%s" % (cwd,prob.name,menv.name)
  if not os.path.exists(filedir):
    os.makedirs(filedir)

  variables = prob.variable_order
  W =dict(map(lambda v: (v,[]), variables))
  for t,z in zip(T,Z):
    for var,value in zip(variables,z):
      W[var].append(value)

  for series_name,values in W.items():
    filepath = "%s/%s.png" % (filedir,series_name);
    plt.plot(T,values,label=series_name)
    plt.savefig(filepath)
    plt.clf()



def plot_diffeq(menv,prob,T,Y):
  cwd = os.getcwd()
  filedir = "%s/BMARK_REF/%s_%s" % (cwd,prob.name,menv.name)
  if not os.path.exists(filedir):
    os.makedirs(filedir)
  variables = prob.variable_order
  Z =dict(map(lambda v: (v,[]), variables))
  for t,y in zip(T,Y):
    z = prob.curr_state(menv,t,y)
    for var,value in zip(variables,z):
      Z[var].append(value)

  for series_name,values in Z.items():
    filepath = "%s/%s.png" % (filedir,series_name);
    print(series_name,len(T),len(values))
    plt.plot(T,values,label=series_name)
    plt.savefig(filepath)
    plt.clf()

def run_diffeq(menv,prob):
  def dt_func(t,vs):
    return prob.next_deriv(menv,t,vs)

  print("[run_diffeq] initializing")
  init_cond = prob.init_state(menv)
  time = menv.sim_time
  n = 1000.0*menv.sim_time
  dt = time/n
  r = ode(dt_func).set_integrator('zvode',method='bdf')
  r.set_initial_value(init_cond,t=0.0)
  T = []
  Y = []
  print("[run_diffeq] running")
  with tqdm.tqdm(total=n) as prog:
    while r.successful() and r.t < time:
        T.append(r.t)
        Y.append(r.y)
        r.integrate(r.t + dt)
        prog.update(int(r.t*1000))

  return T,Y

