'''
type M
type kmol
type s

time t : s

%param a2 : M/s = 15.6
%param a1 : M/s = 156.25
%param K : kmol = 0.000029618

param a1 : M/s = 15.6
param a2 : M/s = 13.32


param K : kmol = 0.0029618


param nu : unit = 2.0015
param beta : unit = 2.5
param gamma : unit = 1.0


param Cv : unit = 1
param Cu : 1/M  = 1
param kdeg : (M/s) = 1

%
output U : unit 
output V : unit 
local UTF : unit
local VTF : unit
local umodif : unit 
%

input IPTG : kmol
def IPTG mag = [0,0.60] kmol


param K2 : unit = 1.0

rel umodif = (U)*(1/((1+(IPTG/K) )^nu))
def umodif mag = [0,15.6] unit

rel UTF = (Cu*a1)*((K2^beta)/((K2^beta) +(V^beta)))
rel VTF = (Cv*a2)*((K2^gamma)/((K2^gamma) + (umodif^gamma)))
%def UTF mag = [0,15.6] unit
%def VTF mag = [0,13.32] unit

%
rel ddt U =  (UTF)/Cu - (kdeg*U) init 0.0
def U mag = [0,15.6] unit
%def ddt U sample 1000 s
%def ddt U speed 1000 ms 

%
rel ddt V = (VTF)/Cv - (kdeg*V) init 0.0
def V mag = [0,13.32] unit 

%def ddt V sample 1000 s
%def ddt V speed 1000 ms 
'''
if __name__ == "__main__":
  import sys
  import os
  sys.path.insert(0,os.path.abspath("../../"))

from lang.prog import MathProg
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs


def model():
  K = 1.0
  params = {
    'a2': 15.6,
    'a1': 156.25,
    'K' : 0.000029618,
    'nu': 2.0015,
    'beta': 2.5,
    'gamma': 1.0,
    'U0': 0.0,
    'V0': 0.0,
    'kdeg': 0.99999999,
    'vtf_tr':15.6,
    'vtf_kf':1.0,
    'vtf_kd':1.0/K,
    'utf_tr':13.32,
    'utf_kf':1.0,
    'utf_kd':1.0/K
  }
  prob = MathProg("gentoggle")
  prob.bind("IPTG",op.ExtVar('PROT'))
  prob.set_interval("PROT",0.0,0.30)
  prob.set_bandwidth("PROT",10)

  umodif_fun = op.Func(['X'],
                       op.Pow(
                         op.Const(1.0),
                         op.Pow(
                           op.Add(
                             op.Const(1.0),
                             op.Mult(
                               op.Const(1.0/params['K']),
                               op.Var('X')
                             )
                           ),
                           op.Const(-params['nu']))
                       ))
  prob.bind("umodif",op.Call([op.Var('IPTG')], umodif_fun))
  prob.set_interval("umodif",0.0,1.0)

  to_beta = op.Func(['P'], op.Pow(op.Var('P'),op.Const(params['beta'])))
  Vbeta = op.Call([op.Var('V')], to_beta)
  prob.bind("Vbeta",Vbeta)
  params['utf_tr_kf'] = params['utf_tr']*params['utf_kf']
  UTF = parse_diffeq('{utf_tr_kf}+{utf_kf}*(-UTF) + {utf_kd}*(-UTF)*Vbeta',
                     'utf_tr',':utf',params)
  prob.bind("UTF",UTF)
  prob.set_interval("UTF",0.0,params['utf_tr'])

  params['vtf_tr_kf'] = params['vtf_tr']*params['vtf_kf']
  VTF = parse_diffeq('{vtf_tr_kf}+{vtf_kf}*(-VTF) + {vtf_kd}*(-VTF)*umodif',
                       'vtf_tr',':vtf',params)
  prob.set_interval("VTF",0.0,params['vtf_tr'])
  prob.bind("VTF",VTF)

  V = parse_diffeq("VTF+{kdeg}*(-V)","U0",":v", params)
  prob.bind("V",V)
  prob.set_interval("V",0,13.32)
  U = parse_diffeq("UTF+{kdeg}*(-U)",'V0',":u", params)
  prob.bind("U",U)
  prob.set_interval("U",0,15.6)
  prob.compile()
  menv = menvs.get_math_env('gentoggle')
  return menv,prob


def execute():
  menv,prob = model()
  T,Y = run_diffeq(menv,prob)
  plot_diffeq(menv,prob,T,Y)


if __name__ == "__main__":
  execute()
