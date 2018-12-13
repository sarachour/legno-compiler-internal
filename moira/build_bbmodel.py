import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import lab_bench.analysis.det_xform as dx
import lab_bench.analysis.stoch_xform as sx
from moira.db import ExperimentDB
import matplotlib.pyplot as plt
from moira.lib.blackbox import BlackBoxModel
import numpy as np
# this consolidates all of the models to build the black box model.
# distortion: unified model, different biases (mean offset)
# noise: unified model, different variances
# time: each run has a delay.

def apply_time_xform_model(align,dataset):
    dataset.output.time_shift(align.delay)
    dataset.output.truncate_before(0)
    dataset.output.truncate_after(dataset.reference.max_time())


def process_noise_model(model,statistics,noise_model,ident,trial):
  paths = model.db.paths
  filepath = model.db.paths.freq_file(ident,trial)
  freqd = fq.FreqDataset.read(filepath)

  print("-> [%s:%d] compute power" % (ident,trial))
  noise_power = freqd.noise().autopower()
  signal_power = freqd.output().autopower()

  print("-> [%s:%d] compute values at model freqs" % (ident,trial))
  noise_values = np.interp(noise_model.freqs, \
                           noise_power.freqs,\
                           np.real(noise_power.phasors))

  signal_values = np.interp(noise_model.freqs, \
                           signal_power.freqs,\
                           np.real(signal_power.phasors))

  assert(len(statistics) == len(noise_values))

  pred_noise = noise_model.apply(signal_values)
  for idx,(n,pn) in enumerate(zip(noise_values,pred_noise)):
    statistics[idx].append(pn-n)

def build_unified_noise_model(model,experiments):
  for ident,trial in experiments:
    filename = model.db.paths.noise_file(ident,trial)
    noise_model = dx.DetLinNoiseXformModel.read(filename)
    # all xforms are the same
    break

  statistics = []
  for _ in range(0,len(noise_model.freqs)):
    statistics.append([])

  for ident,trial in experiments:
    process_noise_model(model,statistics, \
                             noise_model,ident,trial)


  stoch_noise_model = \
                      sx.StochLinNoiseXformModel\
                             .from_deterministic_model(noise_model,
                                                       statistics)

  return stoch_noise_model

def process_distortion_model(model,statistics,sig_xform,ident,trial):
  paths = model.db.paths
  print("-> [%s:%d] read waveforms" % (ident,trial))
  time_xform = dx.DetTimeXform.read(paths.time_xform_file(ident,trial))
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
    sig_xform = dx.DetSignalXform.read(filename)
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
  sig_xform_model = sx.StochSignalXform()
  for ident,trial in experiments:
    process_distortion_model(model,statistics, \
                             sig_xform,ident,trial)


  for i in statistics:
    stat = statistics[i]
    seg = sig_xform.get_segment_by_id(i)
    new_seg = sx.StochSignalXform.StochSegment \
                            .from_deterministic_model(seg,stat['mu'])

    sig_xform_model.add_segment(new_seg)


  return sig_xform_model

def build_unified_time_model(model,experiments):
  delays = []
  warps = []
  for ident,trial in experiments:
    filename = model.db.paths.time_xform_file(ident,trial)
    xform = dx.DetTimeXform.read(filename)
    delays.append(xform.delay)
    warps.append(xform.warp)

  return sx.StochTimeXform(delays,warps)

def execute(model):
  round_no = model.db.last_round()
  experiments = []
  model_file = model.db.paths.model_file(round_no)
  if model.db.paths.has_file(model_file):
    print("model already exists")
    return

  for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
      model.db.get_by_status(ExperimentDB.Status.DENOISED):
    for trial in trials:
      experiments.append((ident,trial))

  time_model = build_unified_time_model(model,experiments)
  bias_model = build_unified_distortion_model(model,experiments)
  noise_model = build_unified_noise_model(model,experiments)

  bbmodel = BlackBoxModel(time_model,bias_model,noise_model)
  bbmodel.write(model_file)
