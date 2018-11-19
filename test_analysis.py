import sys
import lab_bench.analysis.waveform as wf
import matplotlib.pyplot as plt
import os

def generate_plots(rootdir,filename):
    basename = filename.split(".json")[0]

    outdir = "%s/%s" % (rootdir,basename)
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    print("[reading data]")
    filedir = "%s/%s" % (rootdir,filename)
    dataset = wf.EmpiricalData.read(filedir)

    print("[plot timeseries]")
    dataset.plot('%s/orig.png' % outdir)

    print("[align signals]")
    dataset.align()
    dataset.output.trim(1e-4)
    dataset.reference.trim(1e-4)
    print("delay: %s" % dataset.phase_delay)
    print("[plot aligned signals]")
    dataset.plot('%s/align.png' % outdir)


    print("[reference fft]")
    sig_f = dataset.reference.fft()
    print("[plotting]")
    sig_f.plot("%s/ref_fft" % outdir)
    sig_f.write("%s/signal.json" % outdir)

    print("[output fft]")
    out_f = dataset.output.fft()
    print("[plotting]")
    out_f.plot("%s/out_fft" % outdir)
    sig_f.write("%s/both.json" % outdir)

    print("[compute noise]")
    noise = dataset.output.difference(dataset.reference)
    print("[plot noise]")
    plt.clf()
    noise.plot_series()
    plt.savefig('%s/noise.png' % outdir)
    print("=== Noise Frequencies ===")
    print("[noise fft]")
    noise_f = noise.fft()
    print("[noise fft plot]")
    noise_f.plot("%s/noise_fft" % outdir)
    print("[noise fft write]")
    noise_f.write("%s/noise.json" % outdir)

if len(sys.argv) < 2:
    print("usage: test_analysis <dir>")
    sys.exit(1)

path = sys.argv[1]
for path, subdirs, files in os.walk(path):
    for filename in files:
        if filename.endswith(".json") == True and "data" in filename:
            print("==== %s/%s ====" % (path,filename))
            generate_plots(path,filename)
