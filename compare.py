import sys
import os
sys.path.insert(0,os.path.abspath("lab_bench"))

from chip.conc import ConcCirc
import json
from chip.hcdc import board as hdacv2_board
import matplotlib.pyplot as plt

def plot_out(out_data):
  for var,series in out_data.items():
    plt.plot(series['t'],series['v'],label=var)

  plt.legend()
  plt.savefig('out.png')
  plt.clf()

def plot_ref(ref_data):
  for var,series in ref_data.items():
    plt.plot(series['t'],series['v'],label=var)

  plt.legend()
  plt.savefig('ref.png')
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
     plt.plot(sc_t, sc_v,\
              label=('out-%s' % var))

   plt.legend()
   plt.savefig('comp.png')
   plt.clf()

def read_data(path):
  with open(path,'r') as fh:
    objstr = fh.read()
    return json.loads(objstr)

ref = read_data(sys.argv[1])
circ = ConcCirc.from_json(hdacv2_board,
                          read_data(sys.argv[2]))
out_data = {}
ref_data = {}
for idx in range(3,len(sys.argv)):
  out = read_data(sys.argv[3])
  var = out['variable']
  time = out['times']
  values = out['values']
  out_data[var] = {'t':time,'v':values}

ref_data = {}
for var in out_data.keys():
  times = ref['time']
  values = ref[var]
  ref_data[var] = {'t':times, 'v':values}

plot_out(out_data)
plot_ref(ref_data)
plot_compare(out_data,ref_data,circ)
