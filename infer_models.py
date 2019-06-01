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

def to_range(name):
  return chipcmd.RangeType(name)

def group_dataset(data):
  meta = data['metadata']
  block = meta['block']
  chip,tile,slce,inst = meta['loc']['chip'],meta['loc']['tile'], \
                        meta['loc']['slice'],meta['loc']['index']

  grouped_dataset = {}
  for i,grpdata in enumerate(data['groups']['values']):
    group = dict(zip(data['groups']['fields'],grpdata))
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

    grouped_dataset[key]['target'].append(expected['output'])
    grouped_dataset[key]['bias'].append(observed['bias'])
    grouped_dataset[key]['noise'].append(observed['noise'])
    for k,v in params.items():
      if not k in grouped_dataset[key]['params']:
        grouped_dataset[key]['params'][k] = []
      grouped_dataset[key]['params'][k].append(v)

  return block,(chip,tile,slce,inst),grouped_dataset

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



def build_fanout_model(data):
  comp_options = [chipcmd.SignType.options(),
                  chipcmd.SignType.options(),
                  chipcmd.SignType.options()]

  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    gain,bias,bias_unc,noise = infer_model(group_data)

    scale_modes = [to_range(group["in0"])]
    comp_modes = list(itertools.product(*comp_options))
    for comp_mode in comp_modes:
      for scale_mode in scale_modes:
        pass

def build_integ_model(data):
  comp_options = chipcmd.SignType.options()

  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    gain,bias,bias_unc,noise = infer_model(group_data)
    scale_modes = [to_range(group["in0"]),to_range(group["out0"])]
    comp_modes = list(itertools.product(*comp_options))
    for comp_mode in comp_modes:
      for scale_mode in scale_modes:
        pass

def build_dac_model(data):
  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    gain,bias,bias_unc,noise = infer_model(group_data)


def build_mult_model(data):
  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    gain,bias,bias_unc,noise = infer_model(group_data)



def build_model(data):
  meta = data['metadata']
  print("=== BLOCK %s ===" % meta['block'])
  if meta['block'] == 'adc':
    return build_adc_model(data)
  elif meta['block'] == 'fanout':
    return build_fanout_model(data)
  elif meta['block'] == 'integ':
    return build_integ_model(data)
  elif meta['block'] == 'dac':
    return build_dac_model(data)
  elif meta['block'] == 'mult':
    return build_mult_model(data)

  else:
    raise Exception("unhandled: %s" % meta["block"])


parser = argparse.ArgumentParser()
for dirname, subdirlist, filelist in os.walk(CONFIG.DATASET_DIR):
  for fname in filelist:
    if fname.endswith('.json'):
      fpath = "%s/%s" % (dirname,fname)
      with open(fpath,'r') as fh:
        obj = json.loads(fh.read())
        build_model(obj)
