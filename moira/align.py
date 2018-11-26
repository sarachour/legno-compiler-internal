import sys
import lab_bench.analysis.waveform as wf
import matplotlib.pyplot as plt
import os
import shutil
from moira.db import ExperimentDB

def align(model,ident,trial):
    print("-> read waveforms")
    filedir = model.db.timeseries_file(ident,trial)
    dataset = wf.EmpiricalData.read(filedir)
    dataset.plot(model.db.plot_file(ident,trial,'orig'))

    print("-> align waveforms")
    dataset.align()
    delay,score = dataset.align()
    dataset.plot(model.db.plot_file(ident,trial,'align'))

    print("-> fourier transform")
    fds = wf.FreqDataset. \
          from_aligned_time_dataset(-delay,score,dataset)
    freqdata = model.db.freq_file(ident,trial)
    fds.write(freqdata)

def execute(model):
    for ident,trials,inputs,output in \
        model.db.get_by_status(ExperimentDB.Status.RAN):

        for trial in trials:
            align(model,ident,trial)
            model.db.set_status(ident,trial,ExperimentDB.Status.ALIGNED)
