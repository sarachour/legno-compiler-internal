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

def model(self):
  raise NotImplementedError