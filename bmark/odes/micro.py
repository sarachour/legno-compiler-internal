import numpy as np
from scipy.integrate import ode
import matplotlib.pyplot as plt
import math



def micro_simple_osc(name,omega):
  def dt(t,vs):
    P,V = vs[0],vs[1]
    vs[1] = -omega*omega*P
    vs[0] = vs[1]
    return vs

  def ic():
    P,V = 1.0,10.0
    return 10,[P,V]

  def plot(t,y):
    for yser,lbl in zip(y,['P','V','A']):
      plt.plot(t,yser)
      plt.savefig("micro_%s_%s.png" % (name,lbl))
      plt.clf()

  return dt,ic,plot

n = 10000.0
for name,omega in [('one',1),('double',2),('half',0.5)]:
  dt,ic,plot = micro_simple_osc(name,omega)
  time,init_cond = ic()
  r = ode(dt).set_integrator('zvode',method='bdf')
  r.set_initial_value(init_cond,t=0.0)
  dt = time/n
  T = []
  Y = list(map(lambda _: [], init_cond))

  while r.successful() and r.t < time:
    T.append(r.t)
    for idx in range(0,len(r.y)):
      Y[idx].append(float(r.y[idx]))

    r.integrate(r.t + dt)

  print("STOP: %s" % r.t)
  plot(T,Y)

