from chip.model import PortModel, ModelDB
import scipy.optimize
import numpy as np
import math
import matplotlib.pyplot as plt
from scipy.interpolate import interp2d
import itertools

def apply_model(xdata,a,b):
    x = xdata
    result = (a)*(x) + b
    return result

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

def unpack_data(data,keys):
  unpacked = []
  for key in keys:
    n = len(data[key])
    d = np.array(list(map(lambda i: data[key][i], range(n))))
    unpacked.append(d)
  return unpacked

def sub_index(data,inds):
  subdata = []
  for d in data:
    subd = np.array(list(map(lambda i: d[i], inds)))
    subdata.append(subd)
  return subdata

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

def generate_data_2d(in0,in1,error,n=50):
  def get(xi,yi):
    for idx in filter(lambda i: in0[i] == xi and \
                     in1[i] == yi, range(len(in0))):
      return error[idx]
    raise Exception("cannot find??")

  x = np.array(list(set(in0)))
  x.sort()
  y = np.array(list(set(in1)))
  y.sort()
  zd = []
  for yi in y:
    zi = []
    for xi in x:
      zi.append(get(xi,yi))
    zd.append(zi)

  z = np.array(zd)
  fn = interp2d(x,y,z)
  l_in0 = np.linspace(min(in0),max(in0),n)
  l_in1 = np.linspace(min(in1),max(in1),n)
  gen_in0 = []
  gen_in1 = []
  gen_error = []
  for xi in l_in0:
    for yi in l_in1:
      r = fn(xi,yi)[0]
      gen_in0.append(xi)
      gen_in1.append(yi)
      gen_error.append(r)

  return gen_in0,gen_in1,gen_error

def trim_model(data,gain,bias):
  if "in0" in data and "in1" in data:
    in0,in1,target,bias = unpack_data(data,["in0","in1","target","bias"])
    n = len(in0)
    assert(n > 0)
    meas = np.array(list(map(lambda i: bias[i]+target[i], range(n))))
    pred = apply_model(target,gain,bias)
    error = np.array(list(map(lambda i: abs(pred[i]-meas[i]), \
                             range(n))))
    gen_in0,gen_in1,gen_error = generate_data_2d(in0,in1,error)
    def compute_loss(pars):
      return apply_trimming_model([gen_in0,gen_in1], \
                                  gen_error,[(pars[0],pars[1]), \
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
    sub_pred,sub_meas = sub_index([pred,meas], inds)
    error = np.array(list(map(lambda i: abs(sub_pred[i]-sub_meas[i]),\
                              range(m))))
    unc_std = math.sqrt(sum(map(lambda e: e**2, error))/m)
    max_err = max(map(lambda e: abs(e), error))
    return max_err,unc_std,bnds
  else:
    input("helpme")

def plot_input_output_rel(data,gain,bias,bounds):
  if "in0" in data and "in1" in data:
    in0,in1,target,bias = unpack_data(data,["in0","in1","target","bias"])
    n = len(in0)
    meas = np.array(list(map(lambda i: bias[i]+target[i], range(n))))
    pred = apply_model(target,gain,bias)
    error = np.array(list(map(lambda i: abs(pred[i]-meas[i]), range(n))))
    plt.scatter(in0,in1,c=error,s=4.0)
    if not bounds is None:
      plt.axhline(y=-bounds['in0'][0], color='r', linestyle='-')
      plt.axhline(y=bounds['in0'][1], color='r', linestyle='-')
      plt.axvline(x=-bounds['in1'][0], color='r', linestyle='-')
      plt.axvline(x=bounds['in1'][1], color='r', linestyle='-')

    plt.xlabel("in0")
    plt.ylabel("in1")
    plt.savefig("iorel.png")
    plt.clf()


def infer_model(data,adc=False):
  model = PortModel(None,None,None,None,None)

  n = len(data['bias'])
  bias,target,noise,in0 = unpack_data(data,['bias','target','noise','in0'])
  if adc:
    bias = np.array(list(map(lambda i: bias[i]/128.0, range(n))))
    target = np.array(list(map(lambda i: (target[i]-128.0)/128.0, range(n))))
    noise = np.array(list(map(lambda i: noise[i]/(128.0**2), range(n))))

  bnd = {"in0":(1.0,1.0), "in1":(1.0,1.0)}
  if n == 1:
    model.gain = 1.0
    model.bias = bias[0]
    model.uncertainty_bias = 0.0
    model.noise= math.sqrt(sum(map(lambda n: n**2.0, noise))/n)

  elif n > 1:
    meas = np.array(list(map(lambda i: bias[i]+target[i], range(n))))

    (gain,bias),corrs= scipy.optimize.curve_fit(apply_model, target, meas)
    pred = np.array(list(map(lambda i: apply_model(target[i],gain,bias), \
                             range(n))))
    errors = list(map(lambda i: (meas[i]-pred[i])**2.0, range(n)))

    model.gain = gain
    model.bias = bias
    model.noise= math.sqrt(sum(map(lambda n: n**2.0, noise))/n)
    model.bias_uncertainty = math.sqrt(sum(errors)/n)
    max_error =  math.sqrt(max(errors))
    print("max_error=%f" % max_error)
    if max_error > 0.05 and len(in0) > 0:
      new_max_error,new_unc,bnd = trim_model(data,gain,bias)
      print("uncertainty: %f -> %f" % (model.bias_uncertainty,new_unc))
      print("max_error: %f -> %f" % (max_error,new_max_error))
      model.bias_uncertainty = new_unc
      plot_input_output_rel(data,gain,bias,bnd)
      print(model)
      print(bnd)

      input()
  print(model)
  print(bnd)
  return model,bnd

