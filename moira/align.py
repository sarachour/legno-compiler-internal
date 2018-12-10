import sys
import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import matplotlib.pyplot as plt
import os
import shutil
from moira.db import ExperimentDB
from moira.lib.bbmodel import BlackBoxModel
import scipy
import numpy as np
import multiprocessing

def test(paths,ident,trial):
    print("-> [%s:%d] read waveforms" % (ident,trial))
    window = fq.get_window('planck-tukey', {'alpha':0.1})
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    orig = dataset.reference.resample(100000)
    orig.plot_series()
    print("orig(t) power: %s" % orig.power())
    plt.savefig('original')
    plt.clf()
    freq_data = orig.fft(window=window,trend=None)
    print("orig(f) power: %s" % freq_data.power())
    rec = freq_data.inv_fft()
    print("rec(t) power: %s" % rec.power())
    rec.plot_series()
    plt.savefig('recovered')
    plt.clf()
    sys.exit(0)

def align_signal(paths,ident,trial):
    #test(paths,ident,trial)
    # TODO: temporary. next driver run will not be in milliseconds.
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    min_freq = 1.0/(dataset.simulation_time)
    max_freq = 1.0/dataset.output.time_delta()
    # remove sigilent data
    trim_right = dataset.output.time_range()/14*3.8
    print("-> [HACK] trimming four left blocks [%s]" % trim_right)
    dataset.output.truncate_after(dataset.output.max_time()-trim_right)
    print("-> [%s:%d] plot waveforms" % (ident,trial))
    dataset.plot(paths.plot_file(ident,trial,'orig'))

    print("-> [%s:%d] resample waveforms" % (ident,trial))
    npts = 200000
    ref,out = wf.TimeSeries.synchronize_time_deltas(dataset.reference,
                                                    dataset.output,
                                                    npts=npts)

    dataset.set_reference(ref.times,ref.values)
    dataset.set_output(out.times,out.values)
    ref.plot_series()
    out.plot_series()
    plt.savefig('test.png')
    plt.clf()
    print("-> [%s:%d] align waveforms" % (ident,trial))
    window = fq.get_window('planck-tukey', {'alpha':0.1})
    correlation_rank=5
    time_xform = dataset.align(window=window, \
                          correlation_rank=correlation_rank)


    print("[%s:%s] [DISABLED] find time warp function" % (ident,trial))
    #dataset.reference.find_time_warp(dataset.output)

    print("-> [%s:%d] plot aligned waveforms" % (ident,trial))
    dataset.plot(paths.plot_file(ident,trial,'align'))
    time_xform.write(paths.align_file(ident,trial))

def apply_align_model(align,dataset):
    dataset.output.time_shift(align.delay)
    dataset.output.truncate_before(0)
    dataset.output.truncate_after(dataset.reference.max_time())

def xform_build_dataset(paths,ident,trial):
    print("-> [%s:%d] read align model" % (ident,trial))
    align = wf.TimeXform.read(paths.align_file(ident,trial))
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    print("-> [%s:%s] apply alignment" % (ident,trial))
    apply_align_model(align,dataset)
    npts = 200000
    ref,out = wf.TimeSeries.synchronize_time_deltas(dataset.reference,
                                                    dataset.output,
                                                    npts=npts)
    dataset.set_reference(ref.times,ref.values)
    dataset.set_output(out.times,out.values)
    print("-> [%s:%d] plot aligned waveforms" % (ident,trial))
    #dataset.plot(paths.plot_file(ident,trial,'align'))

    n = min(dataset.reference.n(), dataset.output.n())
    nsamps = 10000
    print("-> computed dataset size %s" % n)
    indices = np.random.choice(range(0,n),size=nsamps)
    xs = list(map(lambda i: dataset.reference.ith(i)[1], indices))
    ys = list(map(lambda i: dataset.output.ith(i)[1], indices))
    return xs,ys

def xform_fit_dataset(xs,ys):
    parnames = wf.SignalXform.param_names()
    init = np.random.uniform(size=len(parnames))
    pars,pcov = scipy.optimize.curve_fit(wf.SignalXform.compute,xs,ys,p0=init)
    for name,value in (zip(parnames,pars)):
        print("val %s=%s" % (name,value))
    print(pcov)
    perr = np.sqrt(np.diag(pcov))
    for name,err in zip(parnames,perr):
        print("std %s=%s" % (name,err))

    sig_xform = wf.SignalXform(dict(zip(parnames,pars)))
    return sig_xform

def xform_apply_model(sig_xform,paths,ident,trial):
    print("-> [%s:%d] read align model" % (ident,trial))
    align = wf.TimeXform.read(paths.align_file(ident,trial))
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    print("-> [%s:%s] apply alignment" % (ident,trial))
    apply_align_model(align,dataset)
    print("[%s:%s] apply nonlinearity function" % (ident,trial))
    dataset.reference.apply_signal_xform(sig_xform)
    print("[%s:%s] plot transformed signals" % (ident,trial))
    dataset.plot(paths.plot_file(ident,trial,'disto'))
    print("[%s:%s] write model" % (ident,trial))
    sig_xform.write(paths.xform_file(ident,trial))


def fft_compute_freq(paths,ident,trial):
    print("-> [%s:%d] read time xform model" % (ident,trial))
    time_xform = wf.TimeXform.read(paths.align_file(ident,trial))
    print("-> [%s:%d] read signal xform model" % (ident,trial))
    sig_xform = wf.SignalXform.read(paths.xform_file(ident,trial))
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    print("-> [%s:%s] apply alignment" % (ident,trial))
    apply_align_model(time_xform,dataset)
    print("[%s:%s] apply nonlinearity function" % (ident,trial))
    dataset.reference.apply_signal_xform(sig_xform)
    npts = 4000000
    ref,out = wf.TimeSeries.synchronize_time_deltas(dataset.reference,
                                                    dataset.output,
                                                    npts=npts)
    dataset.set_reference(ref.times,ref.values)
    dataset.set_output(out.times,out.values)

    print("-> [%s:%d] compute noise" % (ident,trial))
    noise = dataset.output\
                   .difference(dataset.reference)

    print("-> [%s:%d] unapply xform" % (ident,trial))
    dataset.reference.unapply_signal_xform(sig_xform)
    print("-> [%s:%d] plot signals" % (ident,trial))
    dataset.set_noise(noise.times,noise.values)
    dataset.plot(paths.plot_file(ident,trial,'fft'))
    print("-> [%s:%d] plot noise" % (ident,trial))
    dataset.noise.plot_series()
    plt.savefig(paths.plot_file(ident,trial,'noise'))
    plt.clf()

    #print("start=%s, end=%s" % (t_start,t_end))
    print("-> [%s:%d] fourier transform" % (ident,trial))
    window = None
    #window = fq.get_window('planck-tukey', {'alpha':0.1})
    window = fq.get_window('hann',{})
    trend = 'constant'
    fds = fq.FreqDataset. \
          from_aligned_time_dataset(dataset,window,trend)
    fds.set_time_transform(time_xform)
    fds.set_signal_transform(sig_xform)
    
    print("=== orig time domain ===")
    print("noise power: %s" % dataset.noise.power())
    print("signal power: %s" % dataset.reference.power())
    print("\=== frequency domain ===")
    print("noise power: %s" % fds.noise().power())
    print("noise autopower: %s" % fds.noise().autopower().power())
    print("signal power: %s" % fds.output().power())
    print("\n")
    print("-> [%s:%d] plot output spectrogram" % (ident,trial))
    fds.output().plot(
        paths.plot_file(ident,trial,'output_ampl'),
        #paths.plot_file(ident,trial,'output_phase'),
        None,
        do_log_x=True,do_log_y=False
    )
    print("-> [%s:%d] plot noise spectrogram" % (ident,trial))
    fds.noise().plot(
        paths.plot_file(ident,trial,'noise_ampl'),
        #paths.plot_file(ident,trial,'noise_phase'),
        None,
        do_log_x=True,do_log_y=False
    )
    #raise Exception("TODO: clip minimum frequency, since we can't measure.")
    #fds.write(paths.freq_file(ident,trial))


def execute_align(model):
    def compute_alignable_experiments():
        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.ALIGNED):
            for trial in trials:
                if not model.db.paths.has_file(model.db.paths.align_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.RAN)

        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.RAN):
            for trial in trials:
                if model.db.paths.has_file(model.db.paths.align_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.ALIGNED)
                    continue

                if not model.db.paths.has_file(model.db.paths.timeseries_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                    ExperimentDB.Status.PENDING)
                    continue

                yield model.db.paths,ident,trial,period,period*n_cycles

    experiments = list(compute_alignable_experiments())
    for db,ident,trial,period,sim_time in experiments:
        print("====  ALIGN %s / %d ==== "% (ident,trial))
        align_signal(db,ident,trial)
        if model.db.paths.has_file(model.db.paths.align_file(ident,trial)):
            model.db.set_status(ident,trial, \
                                ExperimentDB.Status.ALIGNED)

def execute_xform(model):
    def compute_xformable_experiments():
        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.XFORMED):
            for trial in trials:
                if not model.db.paths.has_file(model.db.paths.xform_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.ALIGNED)

        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.ALIGNED):
            for trial in trials:
                if model.db.paths.has_file(model.db.paths.xform_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.XFORMED)
                    continue


                yield model.db.paths,ident,trial,period,period*n_cycles

    def compute_aligned_experiments():
        for ident,trial,_,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.all():
            if model.db.paths.has_file(model.db.paths.align_file(ident,trial)):
                yield model.db.paths,ident,trial,period,period*n_cycles

    experiments = list(compute_xformable_experiments())
    xs, ys = [],[]
    if len(experiments) > 0:
        for db,ident,trial,period,sim_time in compute_aligned_experiments():
            print("====  DATUM %s / %d ==== "% (ident,trial))
            x,y = xform_build_dataset(db,ident,trial)
            xs += x
            ys += y

        xform = xform_fit_dataset(xs,ys)
        for db,ident,trial,period,sim_time in experiments:
            print("====  XFORM %s / %d ==== "% (ident,trial))
            xform_apply_model(xform,db,ident,trial)

def execute_fft(model):
    def compute_fft_experiments():
        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.FFTED):
            for trial in trials:
                if not model.db.paths.has_file(model.db.paths.freq_file(ident,trial)):
                    if not model.db.paths.has_file(model.db.paths.xform_file(ident,trial)):
                        model.db.set_status(ident,trial, \
                                            ExperimentDB.Status.ALIGNED)
                    else:
                        model.db.set_status(ident,trial, \
                                            ExperimentDB.Status.XFORMED)

        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.ALIGNED):
            for trial in trials:
                if model.db.paths.has_file(model.db.paths.freq_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                            ExperimentDB.Status.FFTED)
                elif model.db.paths.has_file(model.db.paths.xform_file(ident_trial)):
                        model.db.set_status(ident,trial, \
                                            ExperimentDB.Status.XFORMED)

        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.XFORMED):
            for trial in trials:
                if model.db.paths.has_file(model.db.paths.freq_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.FFTED)
                    continue


                yield model.db.paths,ident,trial,period,period*n_cycles

    for db,ident,trial,period,sim_time in compute_fft_experiments():
        fft_compute_freq(db,ident,trial)

def execute(model):
    execute_align(model)
    execute_xform(model)
    execute_fft(model)
