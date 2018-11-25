import sys
import lab_bench.analysis.waveform as wf
import matplotlib.pyplot as plt
import os
import shutil

def generate_plots(rootdir,filename):
    basename = filename.split(".json")[0]

    outdir = "%s/%s" % (rootdir,basename)
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir)
    print("-> read waveforms")
    filedir = "%s/%s" % (rootdir,filename)
    dataset = wf.EmpiricalData.read(filedir)

    dataset.plot('%s/orig.png' % outdir)

    print("-> align waveforms")
    dataset.align()
    delay,score = dataset.align()
    dataset.plot('%s/align.png' % outdir)

    fds = wf.FreqDataset.from_aligned_time_dataset(-delay,score,dataset)
    fds.write("%s/freqdp.json" % outdir)
    #dataset.output.trim(1e-4)
    #dataset.reference.trim(1e-4)

if len(sys.argv) < 2:
    print("usage: test_analysis <dir>")
    sys.exit(1)

path = sys.argv[1]
for path, subdirs, files in os.walk(path):
    for filename in files:
        if filename.endswith(".json") == True \
           and "data" in filename:
            print("-> %s/%s" % (path,filename))
            generate_plots(path,filename)
