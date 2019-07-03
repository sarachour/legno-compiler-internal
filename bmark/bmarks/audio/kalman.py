import bmark.bmarks.audio.audio_util as autil

from lang.prog import MathProg
from lang.prog import MathEnv
from ops import op, opparse
from bmark.bmarks.common import *
import bmark.menvs as menvs
import chip.units as units
import chip.hcdc.globals as glb
import numpy as np

def model():
  prob = MathProg("aud-kalman")

  params = {
    'a': 2.0,
    'c': 2.0,
    'r': 1.0,
    'q': 0.0,
    'tc': 5000,
    "X0": 1.0,
    "P0": 1.0,
    "one": 0.9999
  }
  hwtc = 200*1000.0
  actual_tc = params['tc']/hwtc
  for key in ['a', 'q', 'c','r']:
    params[key] *= actual_tc


  #a,b,h = getps(['a','b','c'])
  #r,q = getps(['r','q'])
  #tc1,tc2 = getps(['tc','tc'])
  #u = 0.0
  #z = float(zfun(time))
  #rinv = r**-1.0
  #k = p*h*rinv
  #dx = tc1*(a*x + b*u +k*z-k*h*x)
  #dp = tc2*(2.0*a*p + q -k*k*r)

  params['rinv'] = params['r']**-1
  params['2a'] = params['a']*2.0

  # see extended_kalman_filter notebook

  params['kkrc'] = (params['c']**2)*(params['rinv']**(2))*params['r']
  params['kc'] = params['c']*params['c']*params['rinv']
  params['k'] = params['c']*params['rinv']

  # K = P*b*r**-1
  dX = parse_diffeq('({a}*X)+({k}*P)*({one}*Z)+({kc}*(-P))*({one}*X)', 'X0', ":a",params)
  dP = parse_diffeq('{2a}*P+({kkrc}*(-P))*({one}*P)', "P0", ":b",params)

  lb,ub = autil.set_microphone(prob,"I","Z")
  prob.bind("X", dX)
  prob.set_interval("X", lb,ub)
  prob.bind("P", dP)
  prob.set_interval("P", -1.0, 1.0)
  autil.measure_var(prob,"X","OUT")
  prob.compile()

  menv = autil.math_env(prob)
  return menv,prob
