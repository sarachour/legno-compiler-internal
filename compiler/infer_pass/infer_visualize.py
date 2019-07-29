import matplotlib.pyplot as plt
from compiler.infer_pass.infer_util import get_directory,apply_model
import numpy as np
from scipy.ndimage.filters import gaussian_filter
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import seaborn as sns
import scipy.interpolate

DO_PLOTS = False

def norm(v,vmin,vmax):
  return (v-vmin)/(vmax-vmin)

def heatmap(in0,in1,value,bnd=None):
  x,y,z = [],[],[]
  if bnd is None:
    vmin,vmax = min(value),max(value)
  else:
    vmin,vmax = bnd

  ndims = 2
  if min(in1) == max(in1):
    ndims = 1

  if ndims == 2:
    n = len(in0)
    xs = []
    for i in range(n):
      xs.append([in0[i],in1[i]])

    grid_x, grid_y = np.mgrid[min(in0):max(in0):100j, \
                              min(in1):max(in1):100j]

    grid_z = scipy.interpolate.griddata(points=xs, \
                                        values=value, \
                                        xi=(grid_x,grid_y),
                                        method="cubic")
    plt.imshow(grid_z.T,
               extent=(min(in0),max(in0), \
                       min(in1),max(in1)), \
               origin='lower', \
               norm=Normalize(vmin,vmax))


  else:
    pass

def plot_noise(filename,in0,in1,out,noise):
  if not DO_PLOTS:
    return

  heatmap(in0,in1,noise)
  #plt.xlabel("in0")
  #plt.ylabel("in1")
  plt.savefig(filename)
  plt.clf()


def plot_bias(filename,in0,in1,out,bias):
  if not DO_PLOTS:
    return

  heatmap(in0,in1,np.abs(bias))
  #plt.scatter(in0,in1,c=np.abs(bias),s=4.0)
  #plt.xlabel("in0")
  #plt.ylabel("in1")
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
  if bounds is None:
    heatmap(in0,in1,error)
  else:
    valid = list(map(lambda i: in_bounds(in0[i],in1[i],bounds),range(n)))
    error_valid = list(map(lambda i: error[i] if valid[i] else 0.0, range(n)))
    heatmap(in0,in1,error_valid,bnd=(min(error),max(error)))

  ax.set_xlabel("in0")
  ax.set_ylabel("in1")
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
