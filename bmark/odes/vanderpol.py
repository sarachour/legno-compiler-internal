import numpy as np
from scipy.integrate import ode
import matplotlib.pyplot as plt

# y'' - u(1-y^2)y' + y = 0

def vanderpol():
  def dt(t,vs):
    u = 1.2
    X = vs[0]
    Y = vs[1]

    vs[0] = Y
    vs[1] = u*(1-X**2)*Y - X
    return vs

  def ic():
    X = 0
    Y = 0.5
    time = 100
    return time,[X,Y]


  def plot(t,y):
    name = "vanderpol"
    X = y[0]
    Y = y[1]
    plt.plot(t,X)
    plt.savefig("%s_X.png" % name)
    plt.clf()
    plt.plot(t,Y)
    plt.savefig("%s_Y.png" % name)
    plt.clf()

  return dt,ic,plot

dt,ic,plot = vanderpol()
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

plot(T,Y)
