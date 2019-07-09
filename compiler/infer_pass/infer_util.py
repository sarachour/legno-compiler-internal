from chip.model import PortModel, ModelDB
import numpy as np
import lab_bench.lib.chipcmd.data as chipcmd
import itertools

def tightest_bounds(bnds):
    lb = min(map(lambda b: b[0], bnds))
    ub = min(map(lambda b: b[1], bnds))
    return (lb,ub)

def apply_model(model,xdata):
    x = xdata
    result = (model.gain)*(x) + model.bias
    return result

# A[B[i]]
def indirect_index(data,inds):
  subdata = []
  subd = np.array(list(map(lambda i: data[i], inds)))
  return subd

def get_data_by_mode(dataset,mode):
    modes = dataset['mode']
    inds = list(filter(lambda i: modes[i] == mode, range(len(modes))))
    bias = indirect_index(dataset['bias'],inds)
    noise = indirect_index(dataset['noise'],inds)
    in0 = indirect_index(dataset['in0'],inds)
    in1 = indirect_index(dataset['in1'],inds)
    out = indirect_index(dataset['out'],inds)
    return bias,noise,in0,in1,out

def to_bool(value):
  return chipcmd.BoolType(value).boolean()

def to_sign(name):
  return chipcmd.SignType(name)

def to_loc(obj):
    chip = obj['chip']
    tile = obj['tile']
    slce = obj['slice']
    index = obj['index']
    loc = "(HDACv2,%d,%d,%d,%d)" \
          % (chip,tile,slce,index)
    return loc

def to_range(name):
  return chipcmd.RangeType(name)

