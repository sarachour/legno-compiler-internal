import sys
import os
sys.path.insert(0,os.path.abspath("lab_bench"))

import numpy as np
from util import paths
from chip.conc import ConcCirc
import json
from chip.hcdc import board as hdacv2_board
import matplotlib.pyplot as plt

outpath = sys.argv[1]
dirs = outpath.split("/")
bmark_dir,bmark,outfile = dirs[2],dirs[3],dirs[-1]
ph= paths.PathHandler(bmark_dir,bmark)
bmark,indices,scale_index, menv_name, hwenv_name, var = \
              ph.measured_waveform_file_to_args(outfile)



def plot_out(out_data):
  for var,series in out_data.items():
    plt.plot(series['t'],series['v'],label=var)
    print("times [%s,%s]" % (min(series['t']),max(series['t'])))
    print("values [%s,%s]" % (min(series['v']),max(series['v'])))
    print("avg %s" % np.mean(series['v']))
  plt.legend()
  outfile = ph.plot(bmark,indices, \
                    scale_index, \
                    menv_name, \
                    hwenv_name, \
                    tag='out')


  plt.savefig(outfile)
  plt.clf()

def plot_ref(ref_data):
  for var,series in ref_data.items():
    plt.plot(series['t'],series['v'],label=var)

  plt.legend()
  outfile = ph.plot(bmark,indices, \
                    scale_index, \
                    menv_name, \
                    hwenv_name, \
                    tag='ref')


  plt.savefig(outfile)
  plt.clf()


def plot_compare(out_data,ref_data,circ):
   for var,series in ref_data.items():
     plt.plot(series['t'],series['v'],\
              label=("ref-%s" % var))

   scfs = {}
   for handle,block,loc in hdacv2_board.handles():
     if circ.in_use(block,loc):
       cfg = circ.config(block,loc)
       if cfg.has_label('out'):
         label = cfg.label('out')
         scf = cfg.scf('out')
         scfs[label] = scf
       elif cfg.has_label('in'):
         label = cfg.label('in')
         scf = cfg.scf('in')
         scfs[label] = scf

   for v,scf in scfs.items():
     print("scf[%s] = %s" % (v,scf))

   time_scf= hdacv2_board.time_constant/circ.tau
   print("tau: %s" % circ.tau)
   for var,series in out_data.items():
     sc_t = list(map(lambda t: t/time_scf, series['t']))
     sc_v = list(map(lambda t: t/scfs[var], series['v']))
     avg_v = np.mean(sc_v)
     print("times [%s,%s]" % (min(sc_t),max(sc_t)))
     print("values [%s,%s]" % (min(sc_v)-avg_v,
                               max(sc_v)-avg_v))
     print("avg-value %s]" % (avg_v))

     plt.plot(sc_t, sc_v,\
              label=('out-%s' % var))

   plt.legend()
   outfile = ph.plot(bmark,indices, \
                    scale_index, \
                    menv_name, \
                    hwenv_name, \
                    tag='comp')


   plt.savefig(outfile)
   plt.clf()

def read_data(path):
  with open(path,'r') as fh:
    objstr = fh.read()
    return json.loads(objstr)

ref_file = ph.reference_waveform_file(bmark,menv_name)
circ_file = ph.conc_circ_file(bmark,indices,scale_index)

ref = read_data(ref_file)
circ = ConcCirc.from_json(hdacv2_board,
                          read_data(circ_file))

out_data = {}
ref_data = {}
for var,ref_values in ref.items():
  out_file = ph.measured_waveform_file(bmark,indices,
                                       scale_index,
                                       menv_name,
                                       hwenv_name,
                                       var)
  if ph.has_file(out_file):
    print(out_file)
    out = read_data(out_file)
    meas_time = out['times']
    meas_values = out['values']
    out_data[var] = {'t':meas_time,'v':meas_values}
    ref_data[var] = {'t':ref['time'], 'v':ref_values}

plot_ref(ref_data)
plot_out(out_data)
plot_compare(out_data,ref_data,circ)
