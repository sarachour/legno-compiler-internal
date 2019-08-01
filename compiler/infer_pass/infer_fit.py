import compiler.infer_pass.infer_util as infer_util
import compiler.infer_pass.infer_visualize as infer_vis
from sklearn import svm

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp2d
import scipy.optimize
import math
import sklearn.tree as tree
from scipy import stats

def apply(lambd, data, classes):
  n = len(data)
  idxs = list(filter(lambd, range(n)))
  data_i = list(map(lambda i: data[i], idxs))
  classes_i = list(map(lambda i: classes[i], idxs))
  return data_i,classes_i

def resample(npts,data,classes):
  n = len(data)
  if n == 0:
    return [],[]
  idxs = list(map(lambda _ : np.random.randint(0,n), \
                  range(npts)))
  data_i = list(map(lambda i: data[i], idxs))
  classes_i = list(map(lambda i: classes[i], idxs))
  return data_i,classes_i



def compute_error_metrics(errors):
  std = np.std(errors)
  mean = np.mean(errors)
  mean_unc = mean+std
  max_unc = max(errors)
  return mean_unc,max_unc



def remove_outliers(model,in0,in1,classes):
  def test(x,l,u):
    return x <= u and l <= x

  def error(cls,pred):
    if not cls and pred:
      return 1.0
    elif cls and not pred:
      return 0.2
    else:
      return 0.0

  def cost(pars):
    l0,u0,l1,u1 = pars
    n = len(in0)
    preds = list(map(lambda i: \
                      test(in0[i],l0,u0) and \
                      test(in1[i],l1,u1),
                      range(n)))

    score = sum(map(lambda i: \
                    error(classes[i],preds[i]), range(n)))
    return score

  scf = 0.75
  bounds = [
    (min(in0),min(in0)*scf),
    (max(in0)*scf,max(in0)),
    (min(in1),min(in1)*scf),
    (max(in1)*scf,max(in1)),
  ]
  result = scipy.optimize.brute(cost, bounds, \
                                finish=scipy.optimize.fmin,
                                Ns=5)
  return (result[0],result[1]),(result[2],result[3])

def get_outlier_classifier(error):
  Q1 = np.percentile(error, 25)
  Q3 = np.percentile(error, 75)
  IQR = Q3-Q1
  UB = IQR+Q3
  # we only care about the upper bound
  return UB

def plot_error_distribution(model,error,cutoff):
  if not infer_vis.DO_PLOTS:
    return

  avg_error = np.mean(error)
  std_error = np.std(error)

  plt.hist(error, normed=True, bins=30)
  plt.axvline(x=cutoff,c="red")
  filename = infer_vis.get_plot_name(model,'edist')
  plt.savefig(filename)
  plt.clf()

def plot_outlier(model,in0,in1,errors,cutoff):
  colors = list(map(lambda e: "green" if e <= cutoff else "red", errors))
  plt.scatter(in0,in1,c=colors)
  filename = infer_vis.get_plot_name(model,'outlier')
  plt.savefig(filename)
  plt.clf()

def split_model(model,in0,in1,out,bias,max_unc):
  n = len(in0)
  assert(n > 0)
  meas = np.array(list(map(lambda i: bias[i]+out[i], range(n))))
  pred = infer_util.apply_model(model,out)
  error = np.array(list(map(lambda i: abs(pred[i]-meas[i]), \
                            range(n))))

  adapt_err = get_outlier_classifier(error)
  plot_error_distribution(model,error,adapt_err)
  plot_outlier(model,in0,in1,error,adapt_err)
  classes = list(map(lambda i: error[i] <= adapt_err,range(n)))
  in0bnds,in1bnds = remove_outliers(model,in0,in1,classes)


  bnds = {}
  bnds['in0'] = in0bnds
  bnds['in1'] = in1bnds
  return bnds




def apply_params(xdata,a,b):
    x = xdata
    result = (a)*(x) + b
    return result

def in_bounds(in0,in1,bnds):
  l0,u0 = bnds['in0']
  l1,u1 = bnds['in1']
  if l0 is None or u0 is None \
     or l1 is None or u1 is None:
    return True

  return in0 >= l0 \
    and in0 <= u0 \
    and in1 >= l0 \
    and in1 <= u0


def infer_model(model,in0,in1,out,bias,noise, \
                uncertainty_limit, \
                adc=False,
                required_points=20):

  n = len(out)
  if adc:
    idxs = list(range(n))
    bias = np.array(list(map(lambda i: bias[i]/128.0, idxs)))
    noise = np.array(list(map(lambda i: noise[i]/(128.0**2), idxs)))
    in0 = np.array(list(map(lambda i: in0[i], idxs)))
    in1 = np.array(list(map(lambda i: in1[i], idxs)))
    out = np.array(list(map(lambda i: (out[i]-128.0)/128.0, idxs)))
    n = len(out)

  else:
    idxs = list(filter(lambda i: abs(bias[i]) < 1.3, range(n)))
    bias = np.array(list(map(lambda i: bias[i], idxs)))
    noise = np.array(list(map(lambda i: noise[i], idxs)))
    in0 = np.array(list(map(lambda i: in0[i], idxs)))
    in1 = np.array(list(map(lambda i: in1[i], idxs)))
    out = np.array(list(map(lambda i: out[i], idxs)))
    n = len(out)

  if n == 1:
    model.gain = 1.0
    model.bias = bias[0]
    model.uncertainty_bias = 0.0
    model.noise= math.sqrt(sum(map(lambda n: n**2.0, noise))/n)
    return model

  in0_valid = in0
  in1_valid = in1
  out_valid = out
  noise_valid = noise
  bias_valid = bias
  bnd = {"in0":(None,None), "in1":(None,None)}
  has_outliers = True
  cnt = 0
  max_prune = 0
  while True:
    n = len(in0_valid)
    inds = list(filter(lambda i: in_bounds(in0_valid[i],in1_valid[i],bnd),
                range(n)))
    m = len(inds)
    meas_valid = np.array(list(map(lambda i: out_valid[i] + bias_valid[i], inds)))
    out_valid = np.array(list(map(lambda i: out_valid[i], inds)))
    bias_valid = np.array(list(map(lambda i: bias_valid[i], inds)))
    in0_valid = np.array(list(map(lambda i: in0_valid[i], inds)))
    in1_valid = np.array(list(map(lambda i: in1_valid[i], inds)))
    noise_valid = np.array(list(map(lambda i: noise_valid[i], inds)))
    if m == 0:
      print(model)
      raise Exception("no data")
    new_gain,new_offset,r_value,p_value,std_err = \
                                  stats.linregress(out_valid,meas_valid)
    pred_valid = np.array(list(map(lambda i: \
                                    apply_params(out_valid[i], \
                                                new_gain, \
                                                new_offset), \
                                    range(m))))
    errors_valid = list(map(lambda i: abs(meas_valid[i]-pred_valid[i]), \
                            range(m)))
    new_unc,new_max_error = compute_error_metrics(errors_valid)
    model.gain = new_gain
    model.bias = new_offset
    model.bias_uncertainty = new_unc
    model.noise= math.sqrt(sum(map(lambda n: n**2.0, noise_valid))/(m-1))
    print(model)
    print("  in0=(%s,%s) in1=(%s,%s)" % (bnd['in0'][0],bnd['in0'][1], \
                                          bnd['in1'][0],bnd['in1'][1]))
    if cnt < max_prune and m >= required_points:
      bnd = split_model(model, \
                        in0_valid, \
                        in1_valid, \
                        out_valid, \
                        bias_valid, \
                        uncertainty_limit)
      cnt += 1
    else:
      print("------")
      return bnd



def build_model(model,dataset,mode,max_uncertainty,adc=False):
  bias,noise,in0,in1,out = infer_util \
                           .get_data_by_mode(dataset,mode)
  infer_vis.plot_bias(model,\
                      infer_vis.get_plot_name(model,'bias'), \
                      in0,in1,out,bias)
  infer_vis.plot_noise(model, \
                       infer_vis.get_plot_name(model,'noise'), \
                       in0,in1,out,noise)
  bnd= infer_model(model,in0,in1,out, \
                        bias,noise,max_uncertainty,adc=adc)
  # none can be bnd
  infer_vis.plot_prediction_error(infer_vis.get_plot_name(model,'error'), \
                                  model,None,in0,in1,out,bias)
  infer_vis.plot_prediction_error(infer_vis.get_plot_name(model,'bnd'), \
                                  model,bnd,in0,in1,out,bias)
  plt.close('all')
  return bnd
