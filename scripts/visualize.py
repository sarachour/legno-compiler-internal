import sys
import matplotlib.pyplot as plt
import json

import numpy as np

if len(sys.argv) <= 3:
    print("visualize.py single|batch data.json")

def visualize_json(filename):
    with open(filename,'r') as fh:
        data = json.loads(fh.read())

    title = "simulation results"
    for key,value in data['meta'].items():
        if key == "input":
            title += str(value)

        print("%s = %s" % (key,value))
    time = data['time']
    for series in data['values'].keys():
        values = data['values'][series]
        plt.plot(time,values)

    plt.xlabel("time (su)")
    plt.ylabel("value (su)")
    plt.title(title)

    outfile = filename.split(".json")[0] + ".png"
    plt.savefig(outfile)
    plt.clf()

import os
assert(sys.argv[1] == "batch" or sys.argv[1] == "single")
if sys.argv[1] == "single":
    filename = sys.argv[2]
    visualize_json(filename)

elif sys.argv[1] == "batch":
    filepath = sys.argv[2]
    for root, dirs, files in os.walk(filepath):
        for filename in files:
            if filename.endswith(('json')):
                visualize_json("%s/%s" % (filepath,filename))
