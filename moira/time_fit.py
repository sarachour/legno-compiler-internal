import sys
import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import matplotlib.pyplot as plt
import os
import shutil
from moira.db import ExperimentDB
import scipy
import numpy as np
import multiprocessing


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
    correlation_rank=10
    time_xform = dataset.align(window=window, \
                          correlation_rank=correlation_rank)


    print("[%s:%s] [DISABLED] find time warp function" % (ident,trial))
    #dataset.reference.find_time_warp(dataset.output)

    print("-> [%s:%d] plot time-xformed waveforms" % (ident,trial))
    dataset.plot(paths.plot_file(ident,trial,'align'))
    time_xform.write(paths.time_xform_file(ident,trial))


def execute(model):
    def compute_alignable_experiments():
        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.ALIGNED):
            for trial in trials:
                if not model.db.paths.has_file(model.db.paths.time_xform_file(ident,trial)):
                    model.db.set_status(ident,trial, \
                                        ExperimentDB.Status.RAN)

        for ident,trials,round_no,period,n_cycles,inputs,output,model_id in \
            model.db.get_by_status(ExperimentDB.Status.RAN):
            for trial in trials:
                if model.db.paths.has_file(model.db.paths.time_xform_file(ident,trial)):
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
        if model.db.paths.has_file(model.db.paths.time_xform_file(ident,trial)):
            model.db.set_status(ident,trial, \
                                ExperimentDB.Status.ALIGNED)
