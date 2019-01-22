import numpy as np
from scipy.integrate import ode
import matplotlib.pyplot as plt

# y'' - u(1-y^2)y' + y = 0

def bmmrxn():
  E0 = 4.4
  S0 = 6.4
  def dt(t,vs):
    kr = 1.24
    kf = 0.01
    kd = 1e-3
    ES = vs[0]
    P = vs[3]
    E = E0 - ES - P
    S = S0 - ES - P
    vs[0] =  kf*E*S - kr*ES - kd*ES
    vs[1] =  kr*ES - kf*E*S
    vs[2] =  kr*ES - kf*E*S
    vs[3] = kd*ES
    return vs

  def ic():
    P = float(0)
    ES = float(0)
    E = float(E0)
    S = float(S0)
    time = 1
    return time,[ES,E,S,P]


  def plot(t,y):
    name = "bmmrxn"
    labels = ['ES','E','S','P']
    for yser,lbl in zip(y,labels):
      plt.plot(t,yser)
      plt.savefig("%s_%s.png" % (name,lbl))
      plt.clf()

  return dt,ic,plot

dt,ic,plot = bmmrxn()
time,init_cond = ic()
n = 1000.0

r = ode(dt).set_integrator('zvode',method='bdf')
r.set_initial_value(init_cond,0)
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
