import scripts.visualize.common as common
from scripts.db import MismatchStatus
import numpy as np
import matplotlib.pyplot as plt


def visualize(series,key,executed_only=True):
  data = common.get_data(series,executed_only=executed_only)
  for ser in data.series():
    idents,values = data.get_data(ser,['ident',key],
                           [MismatchStatus.UNKNOWN, MismatchStatus.IDEAL])
    indices = np.argsort(values)
    for i in indices:
      print("   %s: %s" % (idents[i],values[i]))

    print("\n")

def quality_variance():
  series = 'circ_ident'
  data = common.get_data(series,executed_only=True)
  for ser in data.series():
    idents,var,mean = data.get_data(ser,['ident','quality_variance','quality'],
                           [MismatchStatus.UNKNOWN, MismatchStatus.IDEAL])
    pcts = list(map(lambda i: var[i]/mean[i], range(0,len(var))))
    indices = np.argsort(pcts)
    for i in indices:
      print("   %s: %s +- %s [%s%%]" % (idents[i],mean[i],var[i],pcts[i]*100.0))

    print("\n")



def quality_to_speed():
 series = 'circ_ident'
 data = common.get_data(series,executed_only=True)
 for ser in data.series():
   idents,quality_to_time,qualvar,time= data.get_data(ser,['ident', \
                                                           'quality_time_ratio', \
                                                           'quality_variance', \
                                                           'runtime'],
                                                      [MismatchStatus.UNKNOWN, \
                                                       MismatchStatus.IDEAL])
   indices = np.argsort(quality_to_time)
   for i in indices:
     stdev = qualvar[i]/time[i]
     print("   %s: %s std=%s" % (idents[i],quality_to_time[i],stdev))

   print("\n")


def quality():
  series = 'circ_ident'
  data = common.get_data(series,executed_only=True)
  for ser in data.series():
    idents,var,mean = data.get_data(ser,['ident','quality_variance','quality'],
                           [MismatchStatus.UNKNOWN, MismatchStatus.IDEAL])
    pcts = list(map(lambda i: var[i]/mean[i], range(0,len(var))))
    indices = np.argsort(mean)
    for i in indices:
      print("   %s: %s std=%s" % (idents[i],mean[i],var[i]))

    print("\n")


def speed():
  visualize('circ_ident','runtime')

def rank():
  visualize('bmark','rank',executed_only=False)
