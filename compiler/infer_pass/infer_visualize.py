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

  style = plt.get_cmap("magma")
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
    aspect = (max(in0)-min(in0))/(max(in1)-min(in1))
    plt.imshow(grid_z.T,
               extent=(min(in0),max(in0), \
                       min(in1),max(in1)), \
               aspect=aspect,
               origin='lower', \
               norm=Normalize(vmin,vmax),
               cmap=style)

    plt.xlabel("input 0")
    plt.ylabel("input 1")
    plt.colorbar()

  else:
    # strictly monotonic increasing
    n = len(in0)
    zs = []
    xs = []
    ymax = (max(in0)-min(in0))*0.25
    for i in range(n):
      zs.append(value[i])
      zs.append(value[i])
      zs.append(value[i])
      xs.append([in0[i],0.5*ymax])
      xs.append([in0[i],ymax])
      xs.append([in0[i],0.0])

    grid_x, grid_y = np.mgrid[min(in0):max(in0):100j, \
                              0:ymax:20j]

    try:
      grid_z = scipy.interpolate.griddata(points=xs, \
                                          values=zs, \
                                          xi=(grid_x,grid_y),
                                          method="cubic")
      fig = plt.gca()
      aspect = 1
      plt.imshow(grid_z.T,
                 extent=(min(in0),max(in0),0,ymax), \
                 aspect=aspect, \
                 origin='lower', \
                 norm=Normalize(vmin,vmax), \
                 cmap=style)
      plt.ylim((0.25*ymax,0.75*ymax))
      plt.xlabel("input 0")
      fig.axes.yaxis.set_ticklabels([])
      plt.colorbar(orientation='horizontal')
    except Exception as e:
      return

def make_block_identifier(model):
  loc = model.loc.replace("HDACv2,","")
  loc = loc.split("(")[1].split(")")[0]
  return "%s[%s]" % (model.block,loc)

def save_figure(filename):
  plt.tight_layout()
  plt.savefig(filename,bbox_inches='tight')
  plt.clf()

def plot_noise(model,filename,in0,in1,out,noise):
  if not DO_PLOTS:
    return

  title = "%s Noise" % make_block_identifier(model)
  plt.title(title)
  noise_sqrt = np.sqrt(np.array(noise))
  heatmap(in0,in1,noise_sqrt)
  save_figure(filename)


def plot_bias(model,filename,in0,in1,out,bias):
  if not DO_PLOTS:
    return

  title = "%s Bias" % make_block_identifier(model)
  plt.title(title)
  heatmap(in0,in1,np.abs(bias))
  save_figure(filename)

def plot_prediction_error(filename,model,bounds,in0,in1,out,bias):
  if not DO_PLOTS:
    return

  def in_bounds(i0,i1,bnds):
    if bnds['in0'][0] is None or \
       bnds['in0'][1] is None or \
       bnds['in1'][0] is None or \
       bnds['in1'][1] is None:
      return True

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
    title = "%s Error" % make_block_identifier(model)
    plt.title(title)
    heatmap(in0,in1,error, \
            bnd=(0,max(np.abs(bias))))
  else:
    valid = list(map(lambda i: in_bounds(in0[i],in1[i],bounds),range(n)))
    error_valid = list(map(lambda i: error[i] if valid[i] else 0.0, range(n)))
    title = "%s Error w/Clipping" % make_block_identifier(model)
    plt.title(title)
    heatmap(in0,in1,error_valid, \
            bnd=(0,max(np.abs(bias))))

  save_figure(filename)


def get_plot_name(model,tag):
    direc = get_directory(model)
    if not model.handle is None:
      filename = "%s_%s_%s.png" \
                % (model.port,model.handle,tag)
    else:
      filename = "%s_%s.png" \
                % (model.port,tag)

    return "%s/%s" % (direc,filename)
