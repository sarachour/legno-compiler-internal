import cProfile
import json
import zlib
import numpy as np
import binascii
import time
import util.config as CONFIG
import os
from enum import Enum


def array_map(mapfun):
    return np.array(list(mapfun))

def model_format():
    cmd = [
        "{model:w}q{digital_error:f}d{analog_error:f}b", \
        "{model:w}q{digital_error:f}d{analog_error:f}b{bandwidth:d}k" \
    ]
    return cmd

def pack_model(args):
    if not "bandwidth" in args:
        cmd = "{model}q{digital_error}d{analog_error}b"
    else:
        cmd = "{model}q{digital_error}d{analog_error}b{bandwidth}:k"

    return cmd.format(**args)

def unpack_tag(handle):
  method = "unknown"
  i=0
  if handle[i] == 'n':
    method="naive"
  elif handle[i] == 'i':
    method="ideal"
  elif handle[i] == 'x':
    method="physical"
  elif handle[i] == 'z':
    method="partial"

  i += 1
  assert(handle[i] == 'q')
  i += 1
  next_tag = handle[i:].find('d')
  analog = float(handle[i:i+next_tag])
  i += next_tag
  assert(handle[i] == 'd')
  i += 1
  next_tag = handle[i:].find('b')
  digital= float(handle[i:i+next_tag])
  i += next_tag
  assert(handle[i] == 'b')
  i += 1
  if len(handle[i:]) == 0:
      bandwidth = 200
  else:
      bandwidth = float(handle[i:].split('k')[0])
      bandwidth *= 1000
  return method,analog,digital,bandwidth

def randlist(seed,n):
  np.random.seed(seed)
  return list(map(lambda _ : np.random.uniform(-1,1),range(n)))


def mkdir_if_dne(dirname):
    if not os.path.exists(dirname):
        os.makedirs(dirname)

class Timer:

    def __init__(self,name,ph):
        self._runs = []
        self._name = name
        self._paths = ph

    def start(self):
        self._start = time.time()

    def kill(self):
        self._start = None

    def end(self):
        end = time.time()
        self._runs.append(end-self._start)
        self._start = None

    def __repr__(self):
        if len(self._runs) == 0:
            return "%s mean=n/a std=n/a"

        mean = np.mean(self._runs)
        std = np.std(self._runs)
        return "%s mean=%s std=%s" % (self._name,mean,std)

    def save(self):
        filename = self._paths.time_file(self._name)
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

    elif isinstance(m,Enum):
        return m.value
    else:
        return str(m)
