import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp2d
import scipy.optimize
import math

def inds_model_2(in0,in1,pars,n):
  def inside(pt,ival):
    l,s = ival
    succ = pt >= l and pt <= l+s
    #print("%f in [%f,%f] -> %s" % (pt,l,l+s,succ))
    return succ

  a,b = pars
  inds = list(filter(lambda i: \
                  inside(in0[i],a) and \
                  inside(in1[i],b),
                  range(n)))
  return inds

def compute_span(ival):
  l,s = ival
  u = min(1.0,l+s)
  return u-l


def apply_trimming_model(inps,error,pars):
  n = len(error)
  if len(inps) == 2:
    inds = inds_model_2(inps[0],inps[1],pars,n)
    span = compute_span(pars[0]) + compute_span(pars[1])
  else:
    raise Exception("unsupported: 1 input")

  if span > 4:
    return 100
  m = len(inds)
  sub_err = np.array(list(map(lambda i: abs(error[i]), inds)))
  unc_var = sum(sub_err)/m
  unc_std = math.sqrt(unc_var)
  cost=unc_std*2.0+1.0/(span*0.25)
  #print("unc=%f span=%f cost=%f" % (unc_std,span,cost))
  return cost

def find_closest(data,v):
  best = 0
  for d in data:
    if abs(v) > abs(d) \
       and abs(v-d) < abs(best-v):
      best = d
  return best



def trim_model(model,in0,in1,out,bias):
  n = len(in0)
  assert(n > 0)
  meas = np.array(list(map(lambda i: bias[i]+out[i], range(n))))
  pred = infer_util.apply_model(model,out)
  error = np.array(list(map(lambda i: abs(pred[i]-meas[i]), \
                            range(n))))
  def compute_loss(pars):
    return apply_trimming_model([in0,in1], \
                                error,[(pars[0],pars[1]), \
                                       (pars[2],pars[3])])

  bounds = [(-1.0,-0.5),(1.0,2.0),(-1.0,-0.5),(1.0,2.0)]
  result = scipy.optimize.brute(compute_loss, bounds, Ns=5)
  in0l,in0s,in1l,in1s = result
  bnds = {
    'in0':(
      abs(find_closest(in0,in0l)), \
      abs(find_closest(in0,in0l+in0s))
    ),
    'in1':(
      abs(find_closest(in1,in1l)), \
      abs(find_closest(in1,in1l+in1s))
    ),
  }
  inds = inds_model_2(in0,in0,((in0l,in0s),(in1l,in1s)),n)
  m = len(inds)
  sub_pred = infer_util.indirect_index(pred, inds)
  sub_meas = infer_util.indirect_index(meas, inds)
  error = np.array(list(map(lambda i: abs(sub_pred[i]-sub_meas[i]),\
                            range(m))))
  unc_std = math.sqrt(sum(map(lambda e: e**2, error))/m)
  max_err = max(map(lambda e: abs(e), error))
  return max_err,unc_std,bnds


def apply_params(xdata,a,b):
    x = xdata
    result = (a)*(x) + b
    return result

def infer_model(model,in0,in1,out,bias,noise,adc=False):

  n = len(out)
  if adc:
    bias = np.array(list(map(lambda i: bias[i]/128.0, range(n))))
    out = np.array(list(map(lambda i: (out[i]-128.0)/128.0, range(n))))
    noise = np.array(list(map(lambda i: noise[i]/(128.0**2), range(n))))

  bnd = {"in0":(1.0,1.0), "in1":(1.0,1.0)}
  if n == 1:
    model.gain = 1.0
    model.bias = bias[0]
    model.uncertainty_bias = 0.0
    model.noise= math.sqrt(sum(map(lambda n: n**2.0, noise))/n)

  elif n > 1:
    meas = np.array(list(map(lambda i: bias[i]+out[i], range(n))))

    (gain,offset),corrs= scipy \
                       .optimize.curve_fit(apply_params, \
                                           out, meas)
    pred = np.array(list(map(lambda i: \
                             apply_params(out[i],gain,offset), \
                             range(n))))
    errors = list(map(lambda i: (meas[i]-pred[i])**2.0, range(n)))
    print("gain=%f offset=%f" % (gain,offset))
    model.gain = gain
    model.bias = offset
    model.noise= math.sqrt(sum(map(lambda n: n**2.0, noise))/n)
    model.bias_uncertainty = math.sqrt(sum(errors)/n)
    max_error =  math.sqrt(max(errors))
    print(model)
    print("max_error=%f" % max_error)

    if max_error > 0.01:
      new_max_error,new_unc,bnd = trim_model(model,\
                                             in0,in1,out,bias)
      print("uncertainty: %f -> %f" % (model.bias_uncertainty,new_unc))
      print("max_error: %f -> %f" % (max_error,new_max_error))
      model.bias_uncertainty = new_unc
      infer_vis.plot_prediction_error("pred2.png", \
                                      model,bnd,in0,in1,out,bias)
      print(model)
      print(bnd)
      input()

  return bnd

