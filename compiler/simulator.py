import numpy as np
import tqdm
import os
import matplotlib.pyplot as plt
import json
import bmark.diffeqs as diffeqs
from chip.conc import ConcCirc
import compiler.sim_pass.build_sim as buildsim
from scipy.integrate import ode

def evaluate(expr,var_dict={}):
  var_dict['np'] = np
  return eval(expr,var_dict)

def next_state(derivs,variables,values):
  vdict = dict(zip(map(lambda v: "%s_" % v, \
                       variables),values))
  next_vdict = {}
  for v in variables:
    next_vdict[v] = evaluate(derivs[v],vdict)
  result = list(map(lambda v: next_vdict[v], \
                    variables))
  return result


def plot_simulation(menv,conc_circ_path,V,T,Y):
  cwd = os.getcwd()
  conc_circ_file = conc_circ_path.split("outputs/legno")[1]
  filedir = "%s/SIMULATE/%s_%s" % (cwd, \
                                    conc_circ_file,\
                                    menv.name)
  if not os.path.exists(filedir):
    os.makedirs(filedir)

  Z =dict(map(lambda v: (v,[]), V))
  for t,y in zip(T,Y):
    for var,value in zip(V,y):
      Z[var].append(value)

  for series_name,values in Z.items():
      print("%s: %d" % (series_name,len(values)))
  for series_name,values in Z.items():
    filepath = "%s/%s.png" % (filedir,series_name);
    print('plotting %s' % series_name)
    plt.plot(T,values,label=series_name)
    plt.savefig(filepath)
    plt.clf()

def run_simulation(board,conc_circ, \
                   init_conds,derivs,menv):
  var_order = list(init_conds.keys())

  def dt_func(t,vs):
    return next_state(derivs,var_order,vs)

  print(menv.sim_time)
  time = menv.sim_time/conc_circ.tau
  n = 300.0
  dt = time/n

  r = ode(dt_func).set_integrator('zvode', \
                                  method='bdf')

  x0 = list(map(lambda v: eval(init_conds[v]), \
                var_order))
  r.set_initial_value(x0,t=0.0)
  tqdm_segs = 500
  last_seg = 0
  T = []
  Y = []
  with tqdm.tqdm(total=tqdm_segs) as prog:
    while r.successful() and r.t < time:
        T.append(r.t/conc_circ.board.time_constant)
        Y.append(r.y)
        r.integrate(r.t + dt)
        seg = int(tqdm_segs*float(r.t)/float(time))
        if seg != last_seg:
            prog.n = seg
            prog.refresh()
            last_seg = seg

  return var_order,T,Y

def simulate(board,circ_file,bmark):
  menv = diffeqs.get_math_env(bmark)
  with open(circ_file,'r') as fh:
    obj = json.loads(fh.read())
    circ = ConcCirc.from_json(board, \
                              obj)

  init_conds,derivs =  \
                       buildsim.build_simulation(board, \
                                               circ)
  V,T,Y = run_simulation(board,circ, \
                         init_conds,derivs,menv)
  plot_simulation(menv,circ_file,V,T,Y)
