import argparse
import sys
import os
import shutil
import util.config as CONFIG
import lab_bench.lib.chipcmd.data as chipcmd
import json
import itertools
import numpy as np
import math
from chip.model import PortModel, ModelDB
from chip.hcdc.globals import HCDCSubset
from scipy import optimize
import scripts.infer_util as infer_util

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
                              'in0':[],
                              'in1':[],
                              'bias':[],
                              'noise':[],
                              'params':{}}

    expected = dict(zip(data['expected']['fields'], \
                        data['expected']['values'][i]))
    observed = dict(zip(data['observed']['fields'], \
                        data['observed']['values'][i]))
    params = dict(zip(data['params']['fields'], \
                      data['params']['values'][i]))

    key0,key1 = None,None
    for it in filter(lambda k: 'in0' in k, expected.keys()):
      key0 = it
    for it in filter(lambda k: 'in1' in k, expected.keys()):
      key1 = it

    assert(len(grpdata) == len(grpfields))
    grouped_dataset[key]['target'].append(expected['output'])
    if not key0 is None:
      grouped_dataset[key]['in0'].append(expected[key0])
    if not key1 is None:
      grouped_dataset[key]['in1'].append(expected[key1])

    grouped_dataset[key]['bias'].append(observed['bias'])
    grouped_dataset[key]['noise'].append(observed['noise'])
    for k,v in params.items():
      if not k in grouped_dataset[key]['params']:
        grouped_dataset[key]['params'][k] = []
      grouped_dataset[key]['params'][k].append(v)

  loc = "(HDACv2,%d,%d,%d,%d)" % (chip,tile,slce,inst)
  return block,loc,grouped_dataset


def build_adc_model(data):
  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    infer_model,bnd = infer_util.infer_model(group_data,adc=True)
    comp_mode = "*"
    scale_mode = to_range(group['rng'])
    model = PortModel('tile_adc',loc,'out',
                        comp_mode=comp_mode,
                        scale_mode=scale_mode)

    model.set_model(infer_model)
    yield model

    model = PortModel('tile_adc',loc,'in',
                           comp_mode=comp_mode,
                           scale_mode=scale_mode)
    model.set_oprange_scale(*bnd['in0'])
    yield model

def build_fanout_model(data):
  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    infer_model,bnd = infer_util.infer_model(group_data)

    scale_modes = [to_range(group["range-%s" % group['port']])]
    print(group)
    for comp_mode in comp_modes:
      for scale_mode in scale_modes:
        model = PortModel(block,loc,group['port'],
                            comp_mode=comp_mode,
                            scale_mode=scale_mode)
        model.set_model(infer_model)
        yield model

        model = PortModel(block,loc,"in",
                               comp_mode=comp_mode,
                               scale_mode=scale_mode)
        model.set_oprange_scale(*bnd['in0'])
        yield model


def build_integ_model(data):
  comp_options = list(chipcmd.SignType.options())

  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    scale_mode = (to_range(group["range-in0"]), \
                   to_range(group["range-out0"]))
    print("%s scale-mode=%s port=%s" % (loc, \
                                        str(scale_mode), \
                                        group['port']))
    infer_model,bnd = infer_util.infer_model(group_data)
    for comp_mode in comp_options:
      # the initial condition
      if group["port"]== "in1":
        model = PortModel("integrator",loc,'out', \
                            handle=':z[0]', \
                            comp_mode=comp_mode,
                            scale_mode=scale_mode)
        model.set_model(infer_model)
        yield model

        model = PortModel('integrator',loc,'ic', \
                          comp_mode=comp_mode,
                          scale_mode=scale_mode)
        model.set_oprange_scale(*bnd['in1'])
        yield model

      if group["port"]== "out0":
        model = PortModel('integrator',loc,'out', \
                          comp_mode=comp_mode,
                          scale_mode=scale_mode)
        model.set_model(infer_model)
        yield model

        model = PortModel('integrator',loc,'out', \
                          handle=":z",
                          comp_mode=comp_mode,
                          scale_mode=scale_mode)
        yield model

      # the input port
      elif group["port"] == "in0":
        model = PortModel('integrator',loc,'in', \
                          comp_mode=comp_mode,
                          scale_mode=scale_mode)
        model.set_model(infer_model)
        model.set_oprange_scale(*bnd['in0'])
        yield model
        model = PortModel('integrator',loc,'out', \
                          handle=":z'",
                          comp_mode=comp_mode,
                          scale_mode=scale_mode)
        yield model

def build_dac_model(data):
  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    comp_mode = "*"
    scale_mode = ( \
                   to_sign(group['inv']), \
                   to_range(group['rng']) \
    )
    print("comp_mode=%s scale_mode=%s" % (comp_mode,scale_mode))
    infer_model,bnd = infer_util.infer_model(group_data)
    # ignore source
    model = PortModel('tile_dac',loc,'out', \
                        comp_mode=comp_mode, \
                        scale_mode=scale_mode)
    model.set_model(infer_model)
    yield model

    model = PortModel('tile_dac',loc,'in', \
                      comp_mode=comp_mode,
                      scale_mode=scale_mode)
    model.set_oprange_scale(*bnd['in0'])
    yield model

def build_mult_model(data):
  block,loc,grouped_dataset = group_dataset(data)

  for group_data in grouped_dataset.values():
    group = group_data['group']
    if group['vga']:
      scale_mode = (to_range(group["range-in0"]), \
                    to_range(group["range-out0"]))
    else:
      scale_mode = (to_range(group["range-in0"]), \
                    to_range(group["range-in1"]), \
                    to_range(group["range-out0"]))

    print("scale-mode=%s" % str(scale_mode))
    infer_model,bounds = infer_util.infer_model(group_data)
    comp_mode = "vga" if group['vga'] else "mul"
    model = PortModel("multiplier",loc,'out', \
                        comp_mode=comp_mode,
                        scale_mode=scale_mode)
    model.set_model(infer_model)
    yield model

    model = PortModel("multiplier",loc,'in0', \
                         comp_mode=comp_mode,
                         scale_mode=scale_mode)
    model.set_oprange_scale(*bounds['in0'])
    yield model
    model = PortModel("multiplier",loc,'in1', \
                         comp_mode=comp_mode,
                         scale_mode=scale_mode)
    model.set_oprange_scale(*bounds['in1'])
    yield model
    model = PortModel("multiplier",loc,'coeff', \
                         comp_mode=comp_mode,
                         scale_mode=scale_mode)
    model.set_oprange_scale(*bounds['in1'])
    yield model

def build_model(data):
  meta = data['metadata']
  print("=== BLOCK %s %s ===" % (meta['block'], \
                                 ".".join(
                                   map(lambda v: str(v), \
                                       meta['loc'].values()) \
                                 ))
  )
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

def populate_default_models(board):
  print("==== Populate Default Models ===")
  db = ModelDB()
  for blkname in ['tile_in','tile_out', \
                  'chip_in','chip_out', \
                  'ext_chip_in','ext_chip_out']:
    block = board.block(blkname)
    for inst in board.instances_of_block(blkname):
      for port in block.inputs + block.outputs:
        model = PortModel(blkname,inst,port, \
                          comp_mode='*', \
                          scale_mode='*')
        db.put(model)

    for blkname in ['lut']:
      block = board.block(blkname)
      for inst in board.instances_of_block(blkname):
        for port in block.inputs + block.outputs:
          model = PortModel(blkname,inst,port, \
                            comp_mode='*', \
                            scale_mode='*')
          model.bias_uncertainty = 0.0
          model.noise = 0.0
          db.put(model)

def guess_models(board,min_samples=5):
  db = ModelDB()
  locs = {}
  modes = {}
  models = {}

  for model in db.get_all():
    key = (model.block,model.port,model.handle,model.comp_mode)
    if not key in locs:
      locs[key] = []
      models[key] = {}
      modes[key] = {}

    if not model.scale_mode in models[key]:
      models[key][model.scale_mode] = []
      modes[key][model.scale_mode] = []

    locs[key].append(model.loc)
    models[key][model.scale_mode].append(model)
    modes[key][model.scale_mode].append(model.loc)

  pred_models = {}
  for (block,port,handle,comp_mode),scms in models.items():
    pred_models[(block,port,handle,comp_mode)] = {}
    for scale_mode,model_list in scms.items():
      biases = list(map(lambda m: m.bias, model_list))
      noises = list(map(lambda m: m.noise, model_list))
      uncs = list(map(lambda m: m.bias_uncertainty, model_list))
      gains = list(map(lambda m: m.gain, model_list))
      lbs = list(map(lambda m: m.oprange_scale[0], model_list))
      ubs = list(map(lambda m: m.oprange_scale[1], model_list))

      if len(model_list) < min_samples:
        continue
      print("%s.%s [%s] [%s]" % (block,port,comp_mode,scale_mode))
      print("-> median model [%d]" % (len(model_list)))
      model_locs = modes[(block,port,handle,comp_mode)][scale_mode]
      print("%d (unique=%d)" % (len(model_locs),len(set(model_locs))))
      model = PortModel(block,None,port,comp_mode,scale_mode,handle=handle)
      model.bias = np.median(biases)
      model.noise = np.median(noises)
      model.uncertainty_bias = np.median(uncs)
      model.gain = np.median(gains)
      lb,ub = np.median(lbs),np.median(ubs)
      model.set_oprange_scale(lb,ub)
      pred_models[(block,port,handle,comp_mode)][scale_mode] = model

  for (block,port,handle,comp_mode),loc_list in locs.items():
    for loc in loc_list:
      for scm,pred_model in pred_models[(block,port,handle,comp_mode)].items():
        if loc in modes[(block,port,handle,comp_mode)][scm]:
          continue

        print("+ %s[%s].%s [%s] => %s" % (block,loc,port,handle,scm))
        model = PortModel(block,loc,port,comp_mode,scm,handle=handle)
        model.bias = pred_model.bias
        model.noise = pred_model.noise
        model.gain = pred_model.gain
        model.uncertainty_bias = pred_model.uncertainty_bias
        model.set_oprange_scale(*pred_model.oprange_scale)
        print(model)
        db.put(model)

parser = argparse.ArgumentParser(description="Model inference engine")
parser.add_argument('--subset',default='standard',
                    help='component subset to use for compilation')
parser.add_argument('--populate-defaults',action='store_true',
                    help='insert default models for connection blocks')
parser.add_argument('--guess-models',action='store_true',
                    help='guess models')


args = parser.parse_args()
if args.guess_models:
  from chip.hcdc.hcdcv2_4 import make_board
  subset = HCDCSubset(args.subset)
  hdacv2_board = make_board(subset)
  guess_models(hdacv2_board)
  sys.exit(0)

shutil.rmtree(CONFIG.DATASET_DIR)

cmd = "python3 grendel.py --dump-db calibrate.grendel"
print(cmd)
retcode = os.system(cmd)
if retcode != 0:
  raise Exception("could not dump database: retcode=%d" % retcode)

for dirname, subdirlist, filelist in os.walk(CONFIG.DATASET_DIR):
  for fname in filelist:
    if fname.endswith('.json'):
      fpath = "%s/%s" % (dirname,fname)
      with open(fpath,'r') as fh:
        obj = json.loads(fh.read())
        build_model(obj)

if args.populate_defaults:
  from chip.hcdc.hcdcv2_4 import make_board
  subset = HCDCSubset(args.subset)
  hdacv2_board = make_board(subset)
  populate_default_models(hdacv2_board)
