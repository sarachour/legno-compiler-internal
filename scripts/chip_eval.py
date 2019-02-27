import json
import sys
import matplotlib.pyplot as plt

datafile = sys.argv[1]
with open(datafile,'r') as fh:
  obj = json.loads(fh.read())
  print(obj.keys())
  series_name=obj['variable']
  values = obj['values']
  times = obj['times']
  filepath = datafile.split('.json')[0]+'.png'
  plt.plot(times,values,label=series_name)
  plt.savefig(filepath)
  plt.clf()

