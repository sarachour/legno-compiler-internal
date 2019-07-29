import matplotlib.pyplot as plt
from compiler.infer_pass.infer_util import get_directory,apply_model
import numpy as np

DO_PLOTS = False

def heatmap(in0,in1,value,min_val,max_val):
  x,y,z = [],[],[]
  vmin,vmax = min(value),max(value)
  ndims = 2
  if min(in1) == max(in1):
    ndims = 1

  if ndims == 2:
    for i0,i1,value in zip(in0,in1,value):
      norm_value = (value-vmin)/(vmax-vmin)*100.0
      x += [i0]
      y += [i1]
      z += [norm_value]

    PLT.hexbin(x, y, C=z, gridsize=20, cmap=CM.jet, bins=None)


  else:
    raise NotImplementedError

def plot_noise(filename,in0,in1,out,noise):
  if not DO_PLOTS:
    return

  plt.scatter(in0,in1,c=noise,s=4.0)
  plt.xlabel("in0")
  plt.ylabel("in1")
  plt.savefig(filename)
  plt.colorbar()
  plt.clf()


def plot_bias(filename,in0,in1,out,bias):
  if not DO_PLOTS:
    return


  plt.scatter(in0,in1,c=np.abs(bias),s=4.0)
  plt.xlabel("in0")
  plt.ylabel("in1")
  plt.colorbar()
  plt.savefig(filename)
  plt.clf()


def plot_prediction_error(filename,model,bounds,in0,in1,out,bias):
  if not DO_PLOTS:
    return

  def in_bounds(i0,i1,bnds):
    return i0 >= bnds['in0'][0] and \
      i0 <= bnds['in0'][1] and \
      i1 >= bnds['in1'][0] and \
      i1 <= bnds['in1'][1]

  n = len(in0)
  meas = np.array(list(map(lambda i: bias[i]+out[i], range(n))))
  pred = apply_model(model,out)
  error = np.array(list(map(lambda i: abs(pred[i]-meas[i]), range(n))))
  fig, ax = plt.subplots()
  plt.scatter(in0,in1,c=error,s=5.0)
  if bounds is None:
    plt.scatter(in0,in1,c=error,s=5.0)
  else:
    inds = list(filter(lambda i: in_bounds(in0[i],in1[i],bounds),range(n)))
    in0_valid = list(map(lambda i: in0[i], inds))
    in1_valid = list(map(lambda i: in1[i], inds))
    error_valid = list(map(lambda i: error[i], inds))
    plt.scatter(in0_valid,in1_valid,c=error_valid,s=5.0)

  ax.set_xlabel("in0")
  ax.set_ylabel("in1")
  plt.colorbar()
  plt.savefig(filename)
  plt.clf()


def get_plot_name(model,tag):
    direc = get_directory(model)
    if not model.handle is None:
      filename = "%s_%s_%s.png" \
                % (model.port,model.handle,tag)
    else:
      filename = "%s_%s.png" \
                % (model.port,tag)

    return "%s/%s" % (direc,filename)
