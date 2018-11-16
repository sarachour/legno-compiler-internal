import sys
import lab_bench.analysis.waveform as wf
import matplotlib.pyplot as plt

if len(sys.argv) < 3:
    print("usage: test_analysis <dir> <file>")
    empdata=read('lab_bench/data.json')
    sys.exit(0)

outdir = sys.argv[1]
filename = sys.argv[2]

print("[reading data]")
filedir = "%s/%s" % (outdir,filename)
dataset = wf.EmpiricalData.read(filedir)

print("[plot timeseries]")
dataset.plot('%s/orig.png' % outdir)

print("[align signals]")
dataset.align()
print("[plot aligned signals]")
dataset.plot('%s/align.png' % outdir)


print("[reference fft]")
sig_f = dataset.reference.fft()
sig_f.plot("%s/ref_fft" % outdir)

print("[output fft]")
out_f = dataset.output.fft()
out_f.plot("%s/out_fft" % outdir)

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
