from lang.prog import MathEnv
from ops import op, opparse
import chip.hcdc.globals as glb
from enum import Enum

def set_microphone(prob,var,mathvar):
  hwfreq = glb.TIME_FREQUENCY
  sound_freq = 22.0*1000.0
  freq = sound_freq/hwfreq
  prob.set_bandwidth(var, freq)
  prob.set_interval(var,-1.0,1.0)
  prob.bind(mathvar, op.ExtVar(var,loc='E1'))

  return -1.0,1.0

def hwclock_frequency(freq):
    hwfreq = glb.TIME_FREQUENCY
    return freq/hwfreq

def measure_var(prob,invar,outvar):
  prob.bind(outvar,
            op.Emit(op.Mult(op.Const(0.999999), op.Var(invar)), \
                    loc='A0'))

def math_env(prob):
    menv = MathEnv('audenv');
    hwfreq = glb.TIME_FREQUENCY
    time = 0.1
    prob.set_max_sim_time(time*hwfreq)
    menv.set_sim_time(time*hwfreq)
    menv.set_input_time(time*hwfreq)
    return menv

from sympy import exp, Symbol, symbols
import math
from sympy import poly
from bmark.bmarks.common import *


class FilterMethod(Enum):
    BASIC = "basic"
    BUTTER = "butter"
    CHEBY = "chebychev"
    BESSEL = "bessel"

def xfer_fun_to_model(extvar,name,COEFF,POLY):
  sym = lambda i : "%s%d" % (name,i)
  expr = POLY.expand()
  pexpr = poly(expr)
  n = pexpr.degree()
  coeffs = pexpr.all_coeffs()
  stvars = list(map(lambda i : sym(i), range(n)))
  diffeqs = {}
  diffeqs[sym(0)] = [(COEFF,extvar)]
  #print(POLY)
  for i in range(0,n):
    c = -coeffs[i+1]/coeffs[0]
    diffeqs[sym(0)].append((c,sym(i)))

  for i in range(0,n-1):
    diffeqs[sym(i+1)] = [(0.99999999,sym(i))]

  return sym(n-1),diffeqs

def model_to_diffeqs(prob,model,ampl,threshold=1e-3):

  for dv,terms in model.items():
    expr = []
    for c,v in terms:
      var = ("(-%s)" if c < 0 else "(%s)") % v
      if abs(c) >= threshold:
        expr.append("%f*%s" % (abs(c),var))
      #else:
      #  print("skip: %f*%s" % (abs(c),var))
    strexpr = "+".join(expr)
    E = parse_diffeq(strexpr, "IC", ":%s" % dv,
                     {"IC":0.0})
    prob.bind(dv,E)
    prob.set_interval(dv,-ampl,ampl)


def butter(extvar,fvar,freq_cutoff,degree=1):
  s = symbols("s")
  degs = [
    (s+1),
    (s+1)*(s**2+s+1),
    (s**2+0.7654*s+1)*(s**2+1.8478*s+1),
    (s+1)*(s**2+0.6180*s+1)*(s**2+1.6180*s+1),
    (s**2+0.5176*s+1)*(s**2+1.4142*s+1)*(s**2+1.9319*s+1),
    (s+1)*(s**2+0.4450*s+1)*(s**2+1.2470*s+1)*(s**2+1.8019*s+1)
  ]
  wc = hwclock_frequency(freq_cutoff)/(2.0*math.pi)
  expr = degs[degree-1].subs(s,s/wc)
  G0 = 1.0
  return xfer_fun_to_model(extvar,fvar,0.9999,expr)

def cheby(extvar,fvar,freq_cutoff,degree=1):
  #Chebyshev Prototype Functions in Cascade Form with 0.5-dB Ripple (ε=0.3493)
  s = symbols("s")
  degs = [
    (s+1),
    (s+1)*(s**2+s+1),
    0.7157*(s+0.6265)*(s**2+0.6265*s+1.1425),
    0.3579*(s**2+0.3507*s+1.0635)*(s**2+0.8467*s+0.3564),
    0.1789*(s+0.3623)*(s**2+0.2239*s+1.0358)* \
    (s**2+0.5862*s+0.4768),
    0.0895*(s**2+0.1553*s+1.0230)*(s**2+0.4243*s+0.5900) \
    *(s**2+0.5796*s+0.1570)
  ]
  wc = hwclock_frequency(freq_cutoff)/(2.0*math.pi)
  expr = degs[degree-1].subs(s,s/wc)
  G0 = 1.0
  return xfer_fun_to_model(extvar,fvar,0.9999,expr)

def simple(extvar,fvar,freq_cutoff):
  s = symbols("s")
  #Chebyshev Prototype Functions in Cascade Form with 0.5-dB Ripple (ε=0.3493)
  degs = [(s+1),
          (s+1)*(s**2+s+1)
  ]
  wc = hwclock_frequency(freq_cutoff)/(2.0*math.pi)
  expr = degs[0].subs(s,s/wc)
  G0 = 1.0
  return xfer_fun_to_model(extvar,fvar,1.0,expr)

def lpf(extvar,fvar,method,cutoff_freq,degree):
  _method = FilterMethod(method)
  if _method == FilterMethod.CHEBY and degree > 1:
    out,model = cheby(extvar,fvar, \
                      cutoff_freq, \
                      degree=degree)
  elif _method == FilterMethod.BUTTER and degree > 1:
    out,model = butter(extvar,fvar, \
                             cutoff_freq, \
                             degree=degree)
  else:
    out,model = simple(extvar,fvar, \
                       cutoff_freq)
  return out,model
