import sys
import json 
import matplotlib.pyplot as plt

filename = sys.argv[1]
with open(filename,'r') as fh:
    data = json.loads(fh.read())

plt.figure(figsize=(12,6))
for channel in data:
    if channel == '2':
        continue

    time = data[channel]['time'][::500]
    value = data[channel]['voltage'][::500]
    print(len(time))
    plt.plot(time,value,label=channel)

plt.legend()
plt.savefig('figure.png')



