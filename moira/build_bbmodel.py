import lab_bench.analysis.waveform as wf
from moira.db import ExperimentDB
import matplotlib.pyplot as plt
import moira.lib.bbmodel as bbmodel
import numpy as np
# this consolidates all of the models to build the black box model.
# distortion: unified model, different biases (mean offset)
# noise: unified model, different variances
# time: each run has a delay.

def apply_time_xform_model(align,dataset):
    dataset.output.time_shift(align.delay)
    dataset.output.truncate_before(0)
    dataset.output.truncate_after(dataset.reference.max_time())


def build_unified_noise_model(model,experiments):
  raise Exception("unimplemented")

def process_distortion_model(model,statistics,sig_xform,ident,trial):
  paths = model.db.paths
  print("-> [%s:%d] read waveforms" % (ident,trial))
  time_xform = wf.TimeXform.read(paths.time_xform_file(ident,trial))
  filedir = paths.timeseries_file(ident,trial)
  dataset = wf.TimeSeriesSet.read(filedir)
  print("-> [%s:%s] apply time transform" % (ident,trial))
  apply_time_xform_model(time_xform,dataset)
  print("-> [%s:%s] resample signals" % (ident,trial))
  npts = 1000000
  ref,out = wf.TimeSeries.synchronize_time_deltas(dataset.reference,
                                                  dataset.output,
                                                  npts=npts)
  print("-> [%s:%s] get signal transform indices" % (ident,trial))
  indices = list(map(lambda x: sig_xform.get_segment_id(x), \
                     ref.values))
  print("-> [%s:%s] apply signal transform" % (ident,trial))
  ref.apply_signal_xform(sig_xform)
  print("-> [%s:%d] compute noise" % (ident,trial))
  noise = out.difference(ref)


  print("-> [%s:%d] partition noise" % (ident,trial))
  data = []
  for i in range(0,sig_xform.num_segments):
    data.append([])
  for i,v in zip(indices,noise.values):
    data[i].append(v)

  for idx,subarr in enumerate(data):
    print("==== %d ====" % idx)
    print("n: %s" % len(subarr))
    print("mu: %s" % np.mean(subarr))
    print("std: %s" % np.std(subarr))
    if len(subarr) > 0:
      statistics[idx]['mu'].append(np.mean(subarr))
      statistics[idx]['n'].append(len(subarr))
      statistics[idx]['std'].append(np.std(subarr))



def build_unified_distortion_model(model,experiments):
  for ident,trial in experiments:
    filename = model.db.paths.signal_xform_file(ident,trial)
    sig_xform = wf.SignalXform.read(filename)
    # all xforms are the same
    sig_xform.set_bias(0.0)
    break

  assert(not sig_xform is None)

  statistics = {}
  for i in range(0,sig_xform.num_segments):
    statistics[i] = {}
    statistics[i]['mu'] = []
    statistics[i]['std'] = []
    statistics[i]['n'] = []

  idx = 0
  sig_xform_model = bbmodel.SignalXformModel()
  for ident,trial in experiments:
    process_distortion_model(model,statistics, \
                             sig_xform,ident,trial)

  for i in statistics:
    stat = statistics[i]
    seg = sig_xform.get_segment_by_id(i)
    new_seg = bbmodel.SignalXformModel.Segment \
                            .from_xform_segment(seg,stat['mu'])

    sig_xform_model.add_segment(new_seg)


  return sig_xform_model

def build_unified_time_model(model,experiments):
  delays = []
  warps = []
  for ident,trial in experiments:
    filename = model.db.paths.time_xform_file(ident,trial)
    xform = wf.TimeXform.read(filename)
    delays.append(xform.delay)
    warps.append(xform.warp)

  return bbmodel.TimeXformModel(delays,warps)

def execute(model):
  experiments = []
  for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
      model.db.get_by_status(ExperimentDB.Status.DENOISED):
    for trial in trials:
      experiments.append((ident,trial))

  #time_model = build_unified_time_model(model,experiments)
  #bias_model = build_unified_distortion_model(model,experiments)
  noise_model = build_unified_noise_model(model,experiments)
  raise Exception("TODO: infer black box model.")
