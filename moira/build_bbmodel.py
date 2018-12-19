import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import lab_bench.analysis.det_xform as dx
import lab_bench.analysis.stoch_xform as sx
from moira.db import ExperimentDB
import matplotlib.pyplot as plt
import matplotlib
from moira.lib.blackbox import BlackBoxModel
import numpy as np
import itertools
import os
import json


# this consolidates all of the models to build the black box model.
# distortion: unified model, different biases (mean offset)
# noise: unified model, different variances
# time: each run has a delay.

def load_tmpfile(tmpfile):
    if not tmpfile is None and \
       os.path.exists(tmpfile):
        with open(tmpfile,'r') as fh:
            print("-> reading <%s>" % tmpfile)
            data = json.loads(fh.read())
            return data
    return None

def save_tmpfile(tmpfile,obj):
    if not tmpfile is None:
        print("-> writing <%s>" % tmpfile)
        with open(tmpfile,'w') as fh:
            fh.write(json.dumps(obj))

def remove_tmpfile(tmpfile):
    if not tmpfile is None:
        os.remove(tmpfile)


def apply_time_xform_model(align,dataset):
    dataset.output.time_shift(align.delay)
    dataset.output.truncate_before(0)
    dataset.output.truncate_after(dataset.reference.max_time())

def get_round_data(data,round_no):
  els = []
  for round_id in range(0,round_no+1):
    if round_id in data:
      els += data[round_id]

  return np.concatenate(els)

def process_noise_model(model,freqs,ident,trial):
  paths = model.db.paths
  filepath = model.db.paths.freq_file(ident,trial)
  freqd = fq.FreqDataset.read(filepath)

  print("-> [%s:%d] compute power" % (ident,trial))
  noise_power = freqd.noise().autopower()
  signal_power = freqd.output().autopower()

  print("-> [%s:%d] compute values at model freqs" % (ident,trial))
  noise_values = np.interp(freqs, \
                           noise_power.freqs,\
                           np.real(noise_power.phasors))

  if len(signal_power.phasors) == 0:
    signal_values = np.zeros(len(freqs))
  else:
    signal_values = np.interp(freqs, \
                              signal_power.freqs,\
                              np.real(signal_power.phasors))


  return freqs,signal_values,noise_values

def plot_unified_noise_model(model,stoch_model,model_id,\
                             ident,trial,f,x,y):
  def fast_stds(idx):
    mu = stoch_model.mean.apply_one(idx,x[idx])
    std = stoch_model.stdev.apply_one(idx,x[idx])
    dist = (y[idx]-mu)/std
    return 1.0/max(dist,1.0)

  print("[%s:%s] generating predictions" % (ident,trial))
  yp = stoch_model.apply2(f,x)
  print("[%s:%s] plotting variance model" % (ident,trial))
  fig,axs = plt.subplots(3,sharex=True,sharey=True)
  axs[0].loglog(f,y,label='data', alpha=0.5, color='black')

  axs[1].loglog(f,yp.mu+yp.sigma,color='blue',linewidth=1.0)
  axs[1].loglog(f,np.maximum(yp.mu-yp.sigma,min(y)),
                label='variance',color='green',linewidth=1.0)

  axs[2].loglog(f,yp.mu,label='mean',linewidth=1.0,color='red')
  fig.savefig(model.db.paths.plot_file(ident,trial,'npred_m%d' % model_id))
  plt.clf()


  fig = plt.figure()
  ax = plt.gca()
  ax.set_facecolor('black')
  print("[%s:%s] computing intensities" % (ident,trial))
  cmap = matplotlib.cm.get_cmap('inferno')
  intensities = [cmap(fast_stds(idx)) \
                 for idx in range(0,len(f))]

  print("[%s:%s] plotting likelihood model" % (ident,trial))
  ax.set_yscale('log')
  ax.set_xscale('log')
  ax.scatter(f,y,c=intensities,s=0.3)
  # Optionally add a colorbar
  cax, _ = matplotlib.colorbar.make_axes(ax)
  cbar = matplotlib.colorbar. \
         ColorbarBase(cax, cmap=cmap)
  fig.savefig(model.db.paths.plot_file(ident,trial, \
                                       'nlik_m%d' % model_id))
  plt.clf()


def build_unified_noise_model(model,experiments,round_ids):
  det_models = {}
  stoch_models = {}
  for round_no,ident,trial in experiments:
    filename = model.db.paths.noise_file(ident,trial)
    noise_xform = dx.DetNoiseModel.read(filename)
    det_models[round_no] = noise_xform

  xs,fs,ys,ls = {},{},{},{}
  for round_no,ident,trial in experiments:
    noise_model = det_models[round_no]
    f,x,y = process_noise_model(model, \
                                noise_model.freqs, \
                                ident, \
                                trial)

    if not round_no in xs:
      for dict_ in [xs,ys,fs,ls]:
          dict_[round_no] = []

    for dict_,arr in zip([xs,ys,fs,ls],
                         [x,y,f,(ident,trial)]):
      dict_[round_no].append(arr)


  for model_id in round_ids:
    mean_model = det_models[model_id]
    X = get_round_data(xs, model_id).reshape(-1,1)
    Y = get_round_data(ys, model_id).reshape(-1,1)
    F = get_round_data(fs, model_id)
    L = mean_model.map_locs(F)
    YPRED = mean_model.apply2(L,X)
    YVAR = np.sqrt((Y-YPRED)**2)
    print("[%s] fitting variance model" % (model_id))
    locs,M,B,N = dx.DetLinearModel.fit(L,X,YVAR,1)
    var_model = sx.DetNoiseModelVariance(locs,M,B,N)
    stoch_model = sx.StochLinearModel(mean_model,var_model)
    stoch_models[model_id] = stoch_model
    print("[%s] generating plots")
    for round_no in round_ids:
      for (ident,trial),f,x,y in zip(
          ls[round_no],fs[round_no], \
          xs[round_no],ys[round_no]):
        plot_unified_noise_model(model,stoch_model,model_id, \
                                 ident,trial,f,x,y)

  return stoch_models


def process_distortion_model(model,ident,trial):
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
  n = min(ref.n(),out.n())
  ref.truncate_after_samples(n)
  out.truncate_after_samples(n)
  assert(out.n() == ref.n())
  print("-> [%s:%d] compute distortion [%d]" % (ident,trial,n))
  deltas = out.difference(ref)
  assert(deltas.n() == ref.n())
  assert(deltas.n() == out.n())
  return list(ref.times),list(ref.values),list(deltas.values)


def plot_unified_distortion_model(model,stoch_model,model_id,ident,trial,t,x,y):
  def fast_stds(idx,m_inds,v_inds):
    mu = stoch_model.mean.apply_one(m_inds[idx],x[idx])
    std = stoch_model.stdev.apply_one(v_inds[idx],x[idx])
    dist = (x[idx]+y[idx]-mu)/std
    return 1.0/max(dist,1.0)


  print("[%s:%s] generating predictions" % (ident,trial))
  yp = stoch_model.apply2(x,x)
  print("[%s:%s] plotting variance model" % (ident,trial))

  fig,axs = plt.subplots(3,sharex=True,sharey=True)
  axs[0].semilogy(t,y,label='data',linewidth=1.0,alpha=0.6,color='black')

  axs[1].semilogy(t,yp.mu+yp.sigma-x,color='blue',linewidth=1.0)
  axs[1].semilogy(t,yp.mu-yp.sigma-x,
                label='variance',color='green',linewidth=1.0)

  axs[2].semilogy(t,yp.mu-x,label='mean',linewidth=1.0,color='red')
  fig.savefig(model.db.paths.plot_file(ident,trial,'dpred_m%d' % model_id))
  plt.clf()

  fig = plt.figure()
  ax = plt.gca()
  print("[%s:%s] computing intensities" % (ident,trial))
  cmap = matplotlib.cm.get_cmap('inferno')
  mean_indices = stoch_model.mean.map_indices(x)
  var_indices = stoch_model.stdev.map_indices(x)
  intensities = [ cmap(fast_stds(idx,mean_indices,var_indices)) \
                  for idx in range(0,len(x))]

  print("[%s:%s] plotting likelihood model" % (ident,trial))
  ax.set_yscale('log')
  ax.scatter(t,x,c=intensities,s=0.1)
  cax, _ = matplotlib.colorbar.make_axes(ax)
  cbar = matplotlib.colorbar. \
         ColorbarBase(cax, cmap=cmap)
  fig.savefig(model.db.paths.plot_file(ident,trial, \
                                       'dlik_m%d' % model_id))
  plt.clf()

def build_unified_distortion_model(model,experiments,round_ids,plot=False):
  tmpfile = 'data_disto.json'
  det_models = {}
  stoch_models = {}
  xs,ts,ys,ls = {},{},{},{}
  for round_no,ident,trial in experiments:
    filename = model.db.paths.signal_xform_file(ident,trial)
    sig_xform = dx.DetSignalXform.read(filename)
    det_models[round_no] = sig_xform

  data = load_tmpfile(tmpfile)
  if not data is None:
    xs,ts,ys,ls = data
    xs = dict(map(lambda tup: (int(tup[0]),tup[1]), xs.items()))
    ys = dict(map(lambda tup: (int(tup[0]),tup[1]), ys.items()))
    ts = dict(map(lambda tup: (int(tup[0]),tup[1]), ts.items()))
    ls = dict(map(lambda tup: (int(tup[0]),tup[1]), ls.items()))

  else:
    for round_no,ident,trial in experiments:
        sig_xform = det_models[round_no]
        t,x,y = process_distortion_model(model, ident, trial)
        if not round_no in xs:
          for dict_ in [xs,ys,ts,ls]:
            dict_[round_no] = []

        for dict_,arr in zip([xs,ys,ts,ls],
                            [x,y,t,(ident,trial)]):
          dict_[round_no].append(arr)

    save_tmpfile(tmpfile, [xs,ts,ys,ls])

  for model_id in round_ids:
    if not model_id in xs:
      continue
    mean_model = det_models[model_id]
    print("[%s] collect data"% (model_id))
    D = get_round_data(xs, model_id)
    Y = get_round_data(ys, model_id).reshape(-1,1)
    L = mean_model.map_locs(D)
    X = D.reshape(-1,1)
    print("[%s] compute predictions and variance"% (model_id))
    YPRED = mean_model.apply2(L,X)
    YVAR = np.sqrt((Y+X-YPRED)**2)
    print("[%s] fitting variance model" % (model_id))
    locs,M,B,N = dx.DetLinearModel.fit(L,X,YVAR,0)
    var_model = sx.DetSignalXformVariance(locs,M,B,N)
    stoch_model = sx.StochLinearModel(mean_model,var_model)
    stoch_models[model_id] = stoch_model

  if plot:
    for model_id in round_ids:
        stoch_model = stoch_models[model_id]
        for round_no in round_ids:
            if not round_no in xs:
                continue
            for (ident,trial),t,x,y in zip(
                ls[round_no],ts[round_no], \
                xs[round_no],ys[round_no]):
                plot_unified_distortion_model(model,stoch_model,model_id, \
                                            ident,trial,t,x,y)


  remove_tmpfile(tmpfile)
  return stoch_models

def build_unified_time_model(model,experiments,round_ids):
  delays = {}
  warps = {}
  stoch_models = {}
  for round_no,ident,trial in experiments:
    filename = model.db.paths.time_xform_file(ident,trial)
    xform = dx.DetTimeXform.read(filename)
    if not round_no in delays:
      delays[round_no],warps[round_no] = [],[]

    delays[round_no].append([xform.delay])
    warps[round_no].append([xform.warp])

  for round_no in round_ids:
    stoch_models[round_no] = sx.StochTimeXform(
      get_round_data(delays,round_no), \
      get_round_data(warps,round_no)
    )

  return stoch_models

def execute(model):
  n_pending = len(list(itertools.chain( \
    model.db.get_by_status(ExperimentDB.Status.PENDING),
    model.db.get_by_status(ExperimentDB.Status.RAN),
    model.db.get_by_status(ExperimentDB.Status.ALIGNED),
    model.db.get_by_status(ExperimentDB.Status.XFORMED),
    model.db.get_by_status(ExperimentDB.Status.FFTED)
  )))

  if n_pending > 0:
       print("cannot model. experiments pending..")
       return False

  experiments = []
  round_ids = []
  for round_id in model.db.rounds():
    model_file = model.db.paths.model_file(round_id)
    if not model.db.paths.has_file(model_file):
      round_ids.append(round_id)

  if len(round_ids) == 0:
      return

  for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
      model.db.get_by_status(ExperimentDB.Status.DENOISED):
    for trial in trials:
      experiments.append((round_no,ident,trial))

  time_model = build_unified_time_model(model,experiments,round_ids)
  bias_model = build_unified_distortion_model(model, \
                                              experiments,round_ids)

  noise_model = build_unified_noise_model(model,experiments,round_ids)
  for round_id in round_ids:
    model_file = model.db.paths.model_file(round_id)
    bbmodel = BlackBoxModel(time_model[round_id],
                            bias_model[round_id],
                            noise_model[round_id])
    bbmodel.write(model_file)

  return True
