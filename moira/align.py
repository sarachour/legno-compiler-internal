import sys
import lab_bench.analysis.waveform as wf
import lab_bench.analysis.freq as fq
import matplotlib.pyplot as plt
import os
import shutil
from moira.db import ExperimentDB
from moira.lib.bbmodel import BlackBoxModel

def align(model,ident,trial,black_box_model=None):
    print("-> read waveforms")
    filedir = model.db.timeseries_file(ident,trial)
    dataset = wf.EmpiricalData.read(filedir)
    dataset.plot(model.db.plot_file(ident,trial,'orig'))

    print("-> align waveforms")
    phase_model = None if black_box_model is None \
                  else black_box_model.phase_model()
    delay,score = dataset.align(phase_model=phase_model)
    delay,score = dataset.align(phase_model=phase_model)


    noise = dataset.output\
           .difference(dataset.reference)
    t_start,t_end = noise.get_trim()
    noise.trim(t_start,t_end)
    dataset.trim(t_start,t_end)

    dataset.plot(model.db.plot_file(ident,trial,'align'))

    print("start=%s, end=%s" % (t_start,t_end))
    noise.plot_series()
    plt.savefig(model.db.plot_file(ident,trial,'noise'))
    plt.clf()
    print("-> fourier transform")
    fds = fq.FreqDataset. \
          from_aligned_time_dataset(-delay,score,dataset)
    freqdata = model.db.freq_file(ident,trial)
    fds.output.plot(
        model.db.plot_file(ident,trial,'output_ampl'),
        model.db.plot_file(ident,trial,'output_phase'),
        do_log_x=True,do_log_y=True
    )
    fds.noise.plot(
        model.db.plot_file(ident,trial,'noise_ampl'),
        model.db.plot_file(ident,trial,'noise_phase'),
        do_log_x=True,do_log_y=True
    )
    fds.write(freqdata)


def execute(model):
    for ident,trials,round_no,inputs,output,model_id in \
        model.db.get_by_status(ExperimentDB.Status.RAN):
        if not model_id is None:
            bmod = BlackBoxModel.read(model.db.model_file(model_id))
        else:
            bmod = None

        for trial in trials:
            print("==== %s / %d ==== "% (ident,trial))
            if model.db.has_file(model.db.freq_file(ident,trial)):
                model.db.set_status(ident,trial, \
                                    ExperimentDB.Status.ALIGNED)
                continue

            if not model.db.has_file(model.db.timeseries_file(ident,trial)):
                model.db.set_status(ident,trial, \
                                    ExperimentDB.Status.PENDING)
                continue

            align(model,ident,trial,bmod)
            if model.db.has_file(model.db.freq_file(ident,trial)):
                model.db.set_status(ident,trial, \
                                    ExperimentDB.Status.ALIGNED)
