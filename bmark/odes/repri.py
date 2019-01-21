import numpy as np
from scipy.integrate import ode
import matplotlib.pyplot as plt
import math

# y'' - u(1-y^2)y' + y = 0

def repri():
  k_tl = 3.01029995664
  kd_prot = 0.03010299956
  kd_mrna = 0.15051499783
  a0_tr = 0.0005
  a_tr = 0.4995

  K = 40.0
  n = 2.0
  kf_bind = 0.1
  kd_bind = kf_bind/K

  def closed_form(prot):
    result = a_tr*(K**n)/(K**n + prot**n)
    return result

  def dt(t,vs):
    LacLm,clm,TetRm = vs[0:3]
    LacLp,clp,TetRp = vs[3:6]
    ALacLp,Aclp,ATetRp = vs[6:9]

    #ALacLp = closed_form(LacLp)
    #Aclp = closed_form(clp)
    #ATetRp = closed_form(TetRp)

    vs[0] = a0_tr+Aclp-kd_mrna*LacLm
    vs[1] = a0_tr+ATetRp-kd_mrna*clm
    vs[2] = a0_tr+ALacLp-kd_mrna*TetRm

    vs[3] = k_tl*LacLm - kd_prot*LacLp
    vs[4] = k_tl*clm - kd_prot*clp
    vs[5] = k_tl*TetRm - kd_prot*TetRp

    # 2 L + P -> L_2 P
    vs[6] = kf_bind*(a_tr-ALacLp) - \
            kd_bind*ALacLp*LacLp*LacLp

    vs[7] = kf_bind*(a_tr-Aclp) - \
            kd_bind*Aclp*clp*clp

    vs[8] = kf_bind*(a_tr-ATetRp) - \
            kd_bind*ATetRp*TetRp*TetRp
    return vs

  def ic():
    # [0,2.5]
    LacLm = 0
    clm = 2
    TetRm = 0
    # [0,140]
    LacLp = 0
    clp = 0
    TetRp = 0
    ATetRp = a_tr
    Aclp = a_tr
    ALacLp= a_tr
    time = 1000
    return time,[LacLm,clm,TetRm,
                 LacLp,clp,TetRp,
                 ALacLp,Aclp,ATetRp]


  def plot(t,y):
    name = "repri"
    labels = ['LacLm','clm','TetRm','LacLp','clp','TetRp']
    for yser,lbl in zip(y,labels):
      plt.plot(t,yser)
      plt.savefig("%s_%s.png" % (name,lbl))
      plt.clf()

  return dt,ic,plot

dt,ic,plot = repri()
time,init_cond = ic()
n = 10000.0

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
