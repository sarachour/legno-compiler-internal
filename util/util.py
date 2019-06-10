import cProfile
import json
import zlib
import numpy as np
import binascii
import time
import util.config as CONFIG
import os
from enum import Enum

def mkdir_if_dne(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

class Timer:

    def __init__(self,name):
        self._runs = []
        self._name = name

    def start(self):
        self._start = time.time()

    def kill(self):
        self._start = None

    def end(self):
        end = time.time()
        self._runs.append(end-self._start)
        self._start = None

    def __repr__(self):
        mean = np.mean(self._runs)
        std = np.std(self._runs)
        return "%s mean=%s std=%s" % (self._name,mean,std)

    def save(self):
        mkdir_if_dne(CONFIG.TIME_DIR)
        filename = "%s/time_%s.txt" % (CONFIG.TIME_DIR,self._name)
        with open(filename,'w') as fh:
            fh.write("%s\n" % self._name)
            for run in self._runs:
                fh.write("%f\n" % run)

def flatten(dictionary, level = []):
    tmp_dict = {}
    for key, val in dictionary.items():
        if type(val) == dict:
            tmp_dict.update(flatten(val, level + [key]))
        else:
            tmp_dict['.'.join(level + [key])] = val
    return tmp_dict

def unflatten(dictionary):
    resultDict = dict()
    for key, value in dictionary.items():
        parts = key.split(".")
        d = resultDict
        for part in parts[:-1]:
            if part not in d:
                d[part] = dict()
            d = d[part]
        d[parts[-1]] = value
    return resultDict


def partition(boolfn,lst):
    yes = []
    no = []
    for el in lst:
        if boolfn(el):
            yes.append(el)
        else:
            no.append(el)
    return yes,no

def values_in_list(vals,lst):
  for val in vals:
    if not val in lst:
      return False
  return True

def keys_in_dict(keys,dict_):
  for key in keys:
    if not key in dict_:
      return False
  return True

def pos_inf(f):
  return f == float('inf')

def equals(f1,f2):
  return abs(f1-f2) <= 1e-5

def decompress_json(hexstr):
  byte_obj = binascii.unhexlify(hexstr)
  comp_obj = zlib.decompress(byte_obj)
  obj = json.loads(str(comp_obj,'utf-8'))
  return obj

def compress_json(obj):
  byte_obj=json.dumps(obj).encode('utf-8')
  comp_obj = zlib.compress(byte_obj,3)
  strdata = str(binascii.hexlify(comp_obj), 'utf-8')
  return strdata

def truncate(f, n):
  '''Truncates/pads a float f to n decimal places without rounding'''
  s = '{}'.format(f)
  if 'e' in s or 'E' in s:
    return '{0:.{1}f}'.format(f, n)
  i, p, d = s.partition('.')
  return float('.'.join([i, (d+'0'*n)[:n]]))

def profile(fn):
  cp = cProfile.Profile()
  cp.enable()
  fn()
  cp.disable()
  cp.print_stats()
  input("continue.")

def is_inf(v):
  return v == float('inf')

def normalize_mode(m):
    if isinstance(m,list):
        m = tuple(m)

    if isinstance(m,tuple):
        return tuple(map(lambda mi: normalize_mode(mi), m))
    if isinstance(m,Enum):
        return m.value
    else:
        return str(m)
