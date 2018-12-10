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


def apply_time_xform_model(xform,dataset):
    dataset.output.time_shift(xform.delay)
    dataset.output.truncate_before(0)
    dataset.output.truncate_after(dataset.reference.max_time())

def apply_signal_xform_model(dataset,paths,ident,trial):
    print("-> [%s:%d] read time xform model" % (ident,trial))
    time_xform = wf.TimeXform.read(paths.time_xform_file(ident,trial))
    print("-> [%s:%d] read signal xform model" % (ident,trial))
    sig_xform = wf.SignalXform.read(paths.signal_xform_file(ident,trial))
    print("-> [%s:%s] apply time xform model" % (ident,trial))
    apply_time_xform_model(time_xform,dataset)
    print("[%s:%s] apply signal xform model" % (ident,trial))
    dataset.reference.apply_signal_xform(sig_xform)
    return time_xform,sig_xform

def fft_compute_freq(paths,ident,trial):
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    orig_ref = dataset.reference.copy()
    npts = 1000000
    time_xform,sig_xform = \
        apply_signal_xform_model(dataset,paths,ident,trial)
    ref,out = wf.TimeSeries.synchronize_time_deltas(dataset.reference,
                                                    dataset.output,
                                                    npts=npts)
    dataset.set_reference(ref.times,ref.values)
    dataset.set_output(out.times,out.values)

    print("-> [%s:%d] compute noise" % (ident,trial))
    noise = dataset.output\
                   .difference(dataset.reference)
    _,bias,new_values = noise.detrend('constant')
    noise.set_values(new_values)

    print("-> [%s:%d] unapply xform" % (ident,trial))
    orig_ref = orig_ref.resample(ref.n())
    dataset.set_reference(orig_ref.times,orig_ref.values)
    print("-> [%s:%d] plot signals" % (ident,trial))
    dataset.set_noise(noise.times,noise.values)
    dataset.plot(paths.plot_file(ident,trial,'fft'))
    print("-> [%s:%d] plot noise" % (ident,trial))
    dataset.noise.plot_series()
    plt.savefig(paths.plot_file(ident,trial,'noise'))
    plt.clf()

    #print("start=%s, end=%s" % (t_start,t_end))
    print("-> [%s:%d] fourier transform" % (ident,trial))
    #window = fq.get_window('planck-tukey', {'alpha':0.1})
    window = fq.get_window('hann',{})
    fds = fq.FreqDataset. \
          from_aligned_time_dataset(dataset,window,trend=None)
    fds.set_time_transform(time_xform)
    fds.set_signal_transform(sig_xform)
    fds.noise().set_bias(bias)
    print("bias: %s" % bias)
    print("-> [%s:%d] print stats" % (ident,trial))
    auto_noise = fds.noise().autopower()
    auto_output = fds.output().autopower()
    print("=== orig time domain ===")
    print("noise power: %s" % dataset.noise.power())
    print("signal power: %s" % dataset.reference.power())
    print("\=== frequency domain ===")
    print("noise power: %s" % fds.noise().power())
    print("noise autopower: %s" % auto_noise.power())
    print("signal power: %s" % fds.output().power())
    print("signal autopower: %s" % auto_output.power())
    print("\n")
    print("-> [%s:%d] plot output autopower" % (ident,trial))
    auto_output.plot(
        paths.plot_file(ident,trial,'output_mag_auto'),
        None,
        do_log_x=True,do_log_y=False
    )
    print("-> [%s:%d] plot output spectrogram" % (ident,trial))
    fds.output().plot(
        paths.plot_file(ident,trial,'output_mag'),
        paths.plot_file(ident,trial,'output_phase'),
        do_log_x=True,do_log_y=False
    )
    print("-> [%s:%d] plot noise autopower" % (ident,trial))
    auto_noise.plot(
        paths.plot_file(ident,trial,'noise_mag_auto'),
        None,
        do_log_x=True,do_log_y=False
    )
    
    print("-> [%s:%d] plot noise spectrogram" % (ident,trial))
    fds.noise().plot(
        paths.plot_file(ident,trial,'noise_mag'),
        paths.plot_file(ident,trial,'noise_phase'),
        do_log_x=True,do_log_y=False
    )
    #raise Exception("TODO: clip minimum frequency, since we can't measure.")
    fds.write(paths.freq_file(ident,trial))



def execute(model):
    def compute_fft_experiments():
        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.FFTED):
            for trial in trials:
                if not model.db.paths.has_file(model.db.paths.freq_file(ident,trial)):
                    if not model.db.paths.has_file(model.db.paths.signal_xform_file(ident,trial)):
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
                elif model.db.paths.has_file(model.db.paths.signal_xform_file(ident,trial)):
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
