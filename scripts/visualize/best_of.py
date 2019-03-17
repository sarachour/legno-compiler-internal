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
  visualize('circ_ident','quality_variance')


def quality_to_speed():
  visualize('bmark','quality_time_ratio')

def quality():
  visualize('bmark','quality')

def speed():
  visualize('circ_ident','runtime')

def rank():
  visualize('bmark','rank',executed_only=False)
