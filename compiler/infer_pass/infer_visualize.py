import matplotlib.pyplot as plt
from compiler.infer_pass.infer_util import get_directory,apply_model
import numpy as np

DO_PLOTS = False

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


  n = len(in0)
  meas = np.array(list(map(lambda i: bias[i]+out[i], range(n))))
  pred = apply_model(model,out)
  error = np.array(list(map(lambda i: abs(pred[i]-meas[i]), range(n))))
  plt.scatter(in0,in1,c=error,s=5.0)
  if not bounds is None:
    plt.axhline(y=-bounds['in0'][0], color='r', linestyle='-')
    plt.axhline(y=bounds['in0'][1], color='r', linestyle='-')
    plt.axvline(x=-bounds['in1'][0], color='r', linestyle='-')
    plt.axvline(x=bounds['in1'][1], color='r', linestyle='-')

  plt.xlabel("in0")
  plt.ylabel("in1")
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
