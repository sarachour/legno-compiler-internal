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

def align(paths,ident,trial,period,sim_time):
    print("-> [%s:%d] read waveforms" % (ident,trial))
    filedir = paths.timeseries_file(ident,trial)
    dataset = wf.TimeSeriesSet.read(filedir)
    orig = dataset.reference.resample(100000)
    orig.plot_series()
    print("orig(t) power: %s" % orig.power())
    plt.savefig('original')
    plt.clf()
    freq_data = orig.fft(trend=None)
    print("orig(f) power: %s" % freq_data.power())
    rec = freq_data.inv_fft()
    print("rec(t) power: %s" % rec.power())
    rec.plot_series()
    plt.savefig('recovered')
    plt.clf()
    sys.exit(0)

    input("-------")
    # TODO: temporary. next driver run will not be in milliseconds.
    min_freq = 1.0/(dataset.simulation_time)
    max_freq = 1.0/dataset.output.time_delta()
    freq_slack = 1.0
    print("-> Freq Range: sim_time=%f delta=%e [%f, %f]" % (dataset.simulation_time, \
                                                            dataset.output.time_delta(), \
                                                            min_freq,max_freq))
    print("-> [%s:%d] plot waveforms" % (ident,trial))
    dataset.plot(paths.plot_file(ident,trial,'orig'))
    print("-> [%s:%d] plotted waveforms" % (ident,trial))

    print("-> [%s:%d] align waveforms" % (ident,trial))
    nsamps = 100000
    correlation_rank=0
    print("-> [%s:%d] number of samples = %d" % (ident,trial,nsamps))
    delay,score = dataset.align(nsamps,
                                correlation_rank=correlation_rank)

    dataset.plot(paths.plot_file(ident,trial,'align'))

    #print("start=%s, end=%s" % (t_start,t_end))
    print("-> [%s:%d] fourier transform" % (ident,trial))
    noise_waveform, fds = fq.FreqDataset. \
          from_aligned_time_dataset(-delay,dataset,n=100000)

    print("-> [%s:%d] plot noise" % (ident,trial))
    noise_waveform.plot_series()
    plt.savefig(paths.plot_file(ident,trial,'noise'))
    plt.clf()

    print("-> [%s:%d] apply frequency filter" % (ident,trial))
    #fds.noise().apply_filter(min_freq-freq_slack,max_freq+freq_slack)
    rect,recx = fds.output().inv_fft()
    wf.TimeSeries(rect,recx).plot_series()
    plt.savefig(paths.plot_file(ident,trial,'rec_output'))
    plt.clf()

    rect,recx = fds.noise().inv_fft()
    wf.TimeSeries(rect,recx).plot_series()
    plt.savefig(paths.plot_file(ident,trial,'rec_noise'))
    plt.clf()

    #input("plotted inversion. continue")

    print("=== time domain ===")
    print("noise power: %s" % noise_waveform.power())
    print("signal power: %s" % dataset.reference.power())
    print("\=== frequency domain ===")
    print("noise power: %s" % fds.noise().power())
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
    fds.write(paths.freq_file(ident,trial))

def do_align(batch):
    for db,ident,trial,period,sim_time in batch:
        align(db,ident,trial,period,sim_time)


def execute(model):
    def compute_alignable_experiments():
        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.ALIGNED):
            for trial in trials:
                if not model.db.paths.has_file(model.db.paths.freq_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.RAN)

        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.RAN):
            for trial in trials:
                if model.db.paths.has_file(model.db.paths.freq_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.ALIGNED)
                    continue

                if not model.db.paths.has_file(model.db.paths.timeseries_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                    ExperimentDB.Status.PENDING)
                    continue

                yield model.db.paths,ident,trial,period,period*n_cycles

    def batch_experiments(exps,nbatches):
        batches = list(map(lambda _ : [],range(0,nbatches)))
        for idx,exp in enumerate(exps):
            batches[idx%nbatches].append(exp)

        return batches

    nbatches = 1
    pool = multiprocessing.Pool(nbatches)
    experiments = list(compute_alignable_experiments())
    batches = batch_experiments(experiments,nbatches)
    for batch in batches:
        do_align(batch)
    #print("=== performing alignment ===")
    #pool.map(do_align, batches)

    for db,ident,trial,period,sim_time in experiments:
        print("==== %s / %d ==== "% (ident,trial))

        if model.db.has_file(model.db.freq_file(ident,trial)):
            model.db.set_status(ident,trial, \
                                ExperimentDB.Status.ALIGNED)
