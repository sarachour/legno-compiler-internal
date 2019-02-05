import os
import common
import sys
import numpy as np

from sklearn.cluster import MeanShift,estimate_bandwidth

N_BREAKS=6
def compute_new_breaks(all_breaks,nbins=5):
  break_array = np.array(all_breaks).reshape(-1, 1)
  bandwidth = estimate_bandwidth(break_array)
  print("bandwidth: %s" % bandwidth)
  ms = MeanShift(bandwidth=bandwidth*0.25,bin_seeding=True)
  ms.fit(break_array)
  labels = ms.labels_
  new_breaks = ms.cluster_centers_.reshape(-1)
  new_breaks.sort()
  return new_breaks


filedir = sys.argv[1]
all_breaks = []
for dirname, subdirlist, filelist in os.walk(filedir):
       for fname in filelist:
           if fname.endswith('.csv'):
             filename = "%s/%s" % (dirname,fname)
             print("> %s" % filename)
             raw_data = common.load_raw_data(filename)

             X = raw_data['freqs']
             data = common.process_raw_data(raw_data)
             breaks,_ = common.compute_pwls(X,data,n=N_BREAKS)
             all_breaks.append(breaks)

new_breaks = compute_new_breaks(all_breaks)
print(new_breaks)
with open('breaks.txt','w') as fh:
  for new_break in new_breaks:
    fh.write("%s\n" % new_break)
