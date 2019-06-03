import argparse
import sys
import os
import util.config as CONFIG
import lab_bench.lib.chipcmd.data as chipcmd
import json
import itertools
import numpy as np
import scipy.optimize
import math
from chip.model import OutputModel, PortModel, ModelDB

def to_sign(name):
  return chipcmd.SignType(name)

def sign_options():
  return list(chipcmd.SignType.options())

def to_range(name):
  return chipcmd.RangeType(name)

def group_dataset(data):
  meta = data['metadata']
  block = meta['block']
  chip,tile,slce,inst = meta['loc']['chip'],meta['loc']['tile'], \
                        meta['loc']['slice'],meta['loc']['index']

  grouped_dataset = {}
  for i,grpdata in enumerate(data['groups']['values']):
    grpfields = data['groups']['fields']
    group = dict(zip(grpfields,grpdata))
    key = str(grpdata)
    if not key in grouped_dataset:
      grouped_dataset[key] = {'group':group,
                              'target':[],
                              'bias':[],
                              'noise':[],
                              'params':{}}

    expected = dict(zip(data['expected']['fields'], \
                        data['expected']['values'][i]))
    observed = dict(zip(data['observed']['fields'], \
                        data['observed']['values'][i]))
    params = dict(zip(data['params']['fields'], \
                      data['params']['values'][i]))

    assert(len(grpdata) == len(grpfields))
    grouped_dataset[key]['target'].append(expected['output'])
    grouped_dataset[key]['bias'].append(observed['bias'])
    grouped_dataset[key]['noise'].append(observed['noise'])
    for k,v in params.items():
      if not k in grouped_dataset[key]['params']:
        grouped_dataset[key]['params'][k] = []
      grouped_dataset[key]['params'][k].append(v)

  loc = "(HDACv2,%d,%d,%d,%d)" % (chip,tile,slce,inst)
  return block,loc,grouped_dataset

def apply_model(xdata,a,b):
    x = xdata
    result = (a)*(x) + b
    return result

def infer_model(data,adc=False):
  n = len(data['bias'])
  print("n=%f group=%s"%(n,data['group']))
  bias = np.array(list(map(lambda i: data['bias'][i], range(n))))
  target= np.array(list(map(lambda i: data['target'][i], range(n))))
  noise = np.array(list(map(lambda i: data['noise'][i], range(n))))
  if adc:
    bias = np.array(list(map(lambda i: bias[i]/128.0, range(n))))
    target = np.array(list(map(lambda i: (target[i]-128.0)/128.0, range(n))))
    noise = np.array(list(map(lambda i: noise[i]/(128.0**2), range(n))))

  if n == 1:
    gain,bias,unc_std,nz_std = 1.0,bias[0],0.0,math.sqrt(noise[0])

  elif n > 1:
    meas = np.array(list(map(lambda i: bias[i]+target[i], range(n))))
    (gain,bias),corrs= scipy.optimize.curve_fit(apply_model, target, meas)
    pred = np.array(list(map(lambda i: apply_model(target[i],gain,bias), \
                             range(n))))
    unc_var = sum(map(lambda i: (meas[i]-pred[i])**2.0, range(n)))/n
    unc_std = math.sqrt(unc_var)
    nz_var = sum(noise)/n
    nz_std = math.sqrt(nz_var)

  print("gain=%f bias=%f bias_unc=%f noise=%f" % (gain,bias,unc_std,nz_std))
  return gain,bias,unc_std,nz_std

def build_adc_model(data):
  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    gain,bias,bias_unc,noise = infer_model(group_data,adc=True)
    comp_mode = "*"
    scale_mode = to_range(group['rng'])
    model = OutputModel('tile_adc',loc,'out',
                        comp_mode=comp_mode,
                        scale_mode=scale_mode)

    model.bias = bias
    model.bias_uncertainty = bias_unc
    model.noise = noise
    model.gain = gain
    yield model

    model = PortModel('tile_adc',loc,'in',
                           comp_mode=comp_mode,
                           scale_mode=scale_mode)
    yield model

def build_fanout_model(data):
  comp_options = [sign_options(), \
                  sign_options(), \
                  sign_options()]

  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    gain,bias,bias_unc,noise = infer_model(group_data)

    scale_modes = [to_range(group["range-%s" % group['port']])]
    comp_modes = list(itertools.product(*comp_options))
    print(scale_modes,comp_modes)
    for comp_mode in comp_modes:
      for scale_mode in scale_modes:
        model = OutputModel(block,loc,group['port'],
                            comp_mode=comp_mode,
                            scale_mode=scale_mode)
        model.bias = bias
        model.bias_uncertainty = bias_unc
        model.noise = noise
        model.gain = gain
        yield model

        model = PortModel(block,loc,"in",
                               comp_mode=comp_mode,
                               scale_mode=scale_mode)
        yield model

def build_integ_model(data):
  comp_options = chipcmd.SignType.options()

  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    gain,bias,bias_unc,noise = infer_model(group_data)
    scale_mode = (to_range(group["range-in0"]), \
                   to_range(group["range-out0"]))
    for comp_mode in comp_options:
      if group["port"]== "out0":
        model = OutputModel("integrator",loc,'out', \
                            handle=':z[0]', \
                            comp_mode=comp_mode,
                            scale_mode=scale_mode)
        model.bias = bias
        model.bias_uncertainty = bias_unc
        model.noise = noise
        model.gain = gain
        yield model
      else:
        model = PortModel('integrator',loc,'in', \
                          comp_mode=comp_mode,
                          scale_mode=scale_mode)
        yield model
        model = PortModel('integrator',loc,'out', \
                          comp_mode=comp_mode,
                          scale_mode=scale_mode)

        yield model

def build_dac_model(data):
  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    gain,bias,bias_unc,noise = infer_model(group_data)
    comp_mode = to_sign(group['inv'])
    scale_mode = to_range(group['rng'])
    # ignore source
    model = OutputModel('tile_dac',loc,'out', \
                        comp_mode=comp_mode, \
                        scale_mode=scale_mode)
    model.bias = bias
    model.bias_uncertainty = bias_unc
    model.noise = noise
    model.gain = gain
    yield model

    model = PortModel('tile_dac',loc,'in', \
                      comp_mode=comp_mode,
                      scale_mode=scale_mode)
    yield model

def build_mult_model(data):
  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    gain,bias,bias_unc,noise = infer_model(group_data)
    if group['vga']:
      scale_mode = (to_range(group["range-in0"]), \
                    to_range(group["range-out0"]))
    else:
      scale_mode = (to_range(group["range-in0"]), \
                    to_range(group["range-in1"]), \
                    to_range(group["range-out0"]))

    comp_mode = "vga" if group['vga'] else "mult"
    model = OutputModel("multiplier",loc,'out', \
                        comp_mode=comp_mode,
                        scale_mode=scale_mode)
    model.bias = bias
    model.bias_uncertainty = bias_unc
    model.noise = noise
    model.gain = gain
    yield model

    model = PortModel("multiplier",loc,'in0', \
                         comp_mode=comp_mode,
                         scale_mode=scale_mode)
    yield model
    model = PortModel("multiplier",loc,'in1', \
                         comp_mode=comp_mode,
                         scale_mode=scale_mode)
    yield model
    model = PortModel("multiplier",loc,'coeff', \
                         comp_mode=comp_mode,
                         scale_mode=scale_mode)
    yield model

def build_model(data):
  meta = data['metadata']
  print("=== BLOCK %s ===" % meta['block'])
  if meta['block'] == 'adc':
    gen = build_adc_model(data)
  elif meta['block'] == 'fanout':
    gen = build_fanout_model(data)
  elif meta['block'] == 'integ':
    gen = build_integ_model(data)
  elif meta['block'] == 'dac':
    gen = build_dac_model(data)
  elif meta['block'] == 'mult':
    gen = build_mult_model(data)
  elif meta['block'] == 'lut':
    gen = map(lambda i : i, [])
  else:
    raise Exception("unhandled: %s" % meta["block"])


  db = ModelDB()
  for model in gen:
    db.put(model)

parser = argparse.ArgumentParser()
for dirname, subdirlist, filelist in os.walk(CONFIG.DATASET_DIR):
  for fname in filelist:
    if fname.endswith('.json'):
      fpath = "%s/%s" % (dirname,fname)
      with open(fpath,'r') as fh:
        obj = json.loads(fh.read())
        build_model(obj)
