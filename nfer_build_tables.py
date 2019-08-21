from chip.model import PortModel, ModelDB
import numpy as np
import os
from scripts.db import ExperimentDB
from chip.conc import ConcCirc
from scipy.stats.stats import pearsonr
import matplotlib.pyplot as plt
import networkx as nx
from networkx.algorithms import isomorphism
db = ModelDB()

def build_scaffold(circ):
  mapping = {}
  graph = nx.DiGraph()
  for idx,(block,loc,cfg) in enumerate(circ.instances()):
    graph.add_node(idx)
    mapping[(block,loc)] = idx

  for sblk,sloc,sport, \
      dblk,dloc,dport in circ.conns():
    idx0 = mapping[(sblk,sloc)]
    idx1 = mapping[(dblk,dloc)]
    graph.add_edge(idx0,idx1)

  return graph

def build_graph(circ):
  graph = nx.DiGraph()
  for block,loc,cfg in circ.instances():
    graph.add_node((block,loc))

  for sblk,sloc,sport, \
      dblk,dloc,dport in circ.conns():
    graph.add_edge((sblk,sloc),(dblk,dloc))

  return graph

def get_assignments(scaffold,graph):
  GM = isomorphism.GraphMatcher(graph,scaffold)
  is_iso = GM.is_isomorphic()
  if is_iso:
    return GM.mapping
  else:
    return None

def build_parameter_translation(scaffold,circ):
  graph = build_graph(circ)
  assigns = get_assignments(scaffold,graph)
  if assigns is None:
    return None
  xlation = {}
  for block,loc,cfg in circ.instances():
    comp_mode = cfg.comp_mode
    scale_mode = cfg.scale_mode
    for model in db.get_by_block(block,loc,comp_mode,scale_mode):
      index = assigns[(block,loc)]
      key = (index,model.port,model.handle)
      for prop in ['bias','gain','unc']:
        orig_param = "%s.%s" % (key,prop)
        xlate_param = "%s[%s].%s:%s.%s" % (block,loc,model.port, \
                                           model.handle,prop)
        xlation[orig_param] = xlate_param

  return xlation

def get_delta_models(circ,scaffold):
  blacklist = ['tile_in','tile_out', \
               'chip_in','chip_out', \
               'ext_chip_in','ext_chip_out']
  data = {}
  graph = build_graph(circ)
  assigns = get_assignments(scaffold,graph)
  if assigns is None:
    return None

  for block,loc,cfg in circ.instances():
    comp_mode = cfg.comp_mode
    scale_mode = cfg.scale_mode
    if block in blacklist:
      continue

    for model in db.get_by_block(block,loc,comp_mode,scale_mode):
      if not "out" in model.port:
        continue

      identifier = assigns[(model.block,model.loc)]
      key = (identifier,model.port,model.handle)
      assert(not key in data)
      data[key] = {}
      data[key]['bias'] = model.bias
      data[key]['gain'] = model.gain
      data[key]['unc'] = model.bias_uncertainty


  params = {}
  for key,datum in data.items():
    for prop,val in datum.items():
      params['%s.%s' % (key,prop)] = val


  return params

def wrapnan(v):
  if np.isnan(v):
    return 0
  else:
    return v

def benchmark_vis(bmark):
  path = "outputs/legno/extended/%s/conc-circ/" % bmark

  expdb = ExperimentDB()
  qualities_naive = {}
  qualities_fab = {}
  # build up all of the qualities and parameters
  for idx,entry in enumerate(expdb.get_by_bmark(bmark)):
    if not entry.subset == 'extended':
      continue

    key = (entry.subset,str(entry.arco_indices))
    if not key in qualities_naive:
      qualities_naive[key] = []

    if not key in qualities_fab:
      qualities_fab[key] = []

    if "nq" in entry.model:
      qualities_naive[key].append(entry.quality)
      pass

    if "zq" in entry.model:
      qualities_fab[key].append(entry.quality)
      pass

  reductions = []
  errors = []
  for key in qualities_naive.keys():
    assert(key in qualities_fab)
    naive = qualities_naive[key]
    fab = qualities_fab[key]
    for n,f in zip(naive,fab):
      err = f/n
      errors.append(err)

  Q1 = np.percentile(errors, 25)
  Q3 = np.percentile(errors, 75)
  median = np.median(errors)
  print("fabs/naive: median=%f Q1=%f Q3=%f" % (median,Q1,Q3))

'''
def benchmark_vis(bmark):
  path = "outputs/legno/extended/%s/conc-circ/" % bmark
  expdb = ExperimentDB()
  qualities = {}
  circs = {}
  parameters = {}
  scaffolds = {}
  # build up all of the qualities and parameters
  for idx,entry in enumerate(expdb.get_by_bmark(bmark)):
    if not "zq" in entry.model or \
       not entry.subset == 'extended':
      continue

    # read circuit
    circ = ConcCirc.read(None,entry.jaunt_circ_file)
    key = None
    #key = entry.model
    if not key in scaffolds:
      scaffolds[key] = build_scaffold(circ)

    pars = get_delta_models(circ,scaffolds[key])
    if pars is None:
      print("-> skip")
      continue

    if not key in parameters:
      parameters[key] = dict(map(lambda k : (k,[]),pars.keys()))
      qualities[key] = []
      circs[key] = []

    for param,val in pars.items():
      parameters[key][param].append(val)

    qualities[key].append(entry.quality)
    circs[key].append(entry.jaunt_circ_file)

  maxval = None
  best_par = None
  for model,circ_files in circs.items():
    circ_file = circ_files[0]
    circ = ConcCirc.read(None,circ_file)
    xlation = build_parameter_translation(scaffolds[model],circ)
    print("  === %s ====" % model)
    print("  file: %s" % circ_file)
    print("  n:  %s" % len(qualities[model]))
    params = list(parameters[model])
    corrs = list(map(lambda p: wrapnan(np.corrcoef(qualities[model], \
                                                   parameters[model][p])[0][1]), \
    params))
    best_index = np.argmax(abs(np.array(corrs)))
    best_par = params[best_index]
    best_corr = corrs[best_index]
    print("  best par:  %s" % xlation[best_par])
    print("  best corr: %s" % best_corr)
    print("  quality: %s +/- %s" % (np.mean(qualities[model]), \
                                  np.std(qualities[model])))


'''
def delta_model_vis_breakdown():
  by_block = {}
  for model in db.get_all():
    if not model.block == "multiplier" or \
       not model.port == "out":
      continue

    key = (model.comp_mode,model.scale_mode)
    if not key in by_block:
      by_block[key] ={
        'noise':[],'gain':[],
        'bias':[],'uncertainty':[]
      }

    by_block[key]['noise'] \
      .append(np.sqrt(model.noise))
    by_block[key]['gain'] \
      .append(model.gain)
    by_block[key]['bias'] \
      .append(model.bias)
    by_block[key]['uncertainty'] \
      .append(model.bias_uncertainty)


  for (comp_mode,scale_mode),data \
      in by_block.items():
    print("----")
    for prop,datum in data.items():
      mean = np.mean(datum)
      stdev = np.std(datum)
      print("%s] %s.%s = %f \pm %f" % \
            (prop,comp_mode,scale_mode, \
             mean,stdev))



def delta_model_vis_basic():
  by_block = {}
  save = [
    ('tile_adc','out',None),
    ('tile_dac','out',None),
    ('fanout','out0',None),
    ('integrator','out',':z[0]'),
    ('multiplier','out',None),
  ]

  for model in db.get_all():
    key = (model.block,model.port,model.handle)
    if not key in by_block:
      by_block[key] = {
        'noise':[],'gain':[],
        'bias':[],'uncertainty':[]
      }

    by_block[key]['noise'] \
      .append(np.sqrt(model.noise))
    by_block[key]['gain'] \
      .append(model.gain)
    by_block[key]['bias'] \
      .append(model.bias)
    by_block[key]['uncertainty'] \
      .append(model.bias_uncertainty)


  for (block,port,handle),data \
      in by_block.items():
    print("----")
    for prop,datum in data.items():
      mean = np.mean(datum)
      stdev = np.std(datum)
      if (block,port,handle) in save:
        print("%s] %s.%s:%s = %f \pm %f" % \
              (prop, block,port,handle,mean,stdev))


delta_model_vis_basic()
sys.exit(0)
delta_model_vis_breakdown()
bmarks = ['vanderpol','pend','spring','pend-nl','spring-nl','micro-osc', \
          'heat1d-g4','kalman-const','robot','smmrxn','bont','gentoggle', \
          'closed-forced-vanderpol']
for bmark in bmarks:
  print("====== %s ======" % bmark)
  benchmark_vis(bmark)

