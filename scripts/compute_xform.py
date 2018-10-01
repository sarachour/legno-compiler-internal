import sys
import matplotlib.pyplot as plt
import json
import os
from sklearn import linear_model
import numpy as np

if len(sys.argv) <= 2:
    print("compute_xform.py out_dir")

directory = sys.argv[1]
points_x = []
points_y = []
for filename in os.listdir(directory):
    if filename.endswith(".json"):
        with open("%s/%s" % (directory,filename),'r') as fh:
            data = json.loads(fh.read())
            in_val = data['meta']['input']['INP']
            pos_vals = data['values']['OUT+']
            neg_vals = data['values']['OUT-']

            for pos_val,neg_val in zip(pos_vals,neg_vals):
                points_x.append(float(in_val))
                points_y.append((pos_val+neg_val)/2.0)

print("=== RANGE ===")
print("MIN: %d" % min(points_y))
print("MAX: %d" % max(points_y))
print("=== REGRESSION ===")
m,b = np.polyfit(points_y, points_x, 1)
print("SCALE=%s" % m)
print("OFFSET=%s" % b)
