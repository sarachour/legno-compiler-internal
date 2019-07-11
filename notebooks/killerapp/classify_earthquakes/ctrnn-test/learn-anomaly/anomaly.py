from enum import Enum
import random

class Category(Enum):
  ANOMALY = "anomaly"
  NORMAL = "normal"

  def to_code(self):
    if Category.ANOMALY == self:
      return 1.0
    else:
      return 0.0

class RNNAnomaly():
  ANOMALY=1
  NORMAL=0

  def __init__(self,n,n_tests):
    self.n = n
    self.num_tests = n_tests

  def generate_anomaly(self):
    raise NotImplementedError

  def generate_normal(self):
    raise NotImplementedError

  def get_anomaly(self):
    seq = list(self.generate_anomaly())
    return seq,Category.ANOMALY.to_code()

  def get_normal(self):
    seq = list(self.generate_normal())
    return seq,Category.NORMAL.to_code()


  def generate_dataset(self):
    for i in range(self.num_tests):
      if i % 2 == 0:
        yield self.get_anomaly()
      else:
        yield self.get_normal()

  def error(self,clazz,output):
    return abs(round(output-clazz))

class NoiseRNNAnomaly(RNNAnomaly):
  def __init__(self,n,n_tests):
    RNNAnomaly.__init__(self,n,n_tests)

  def generate_anomaly(self):
    seq = map(lambda i : random.uniform(0.0,1), range(0,self.n))
    return seq

  def generate_normal(self):
    seq = map(lambda i : random.uniform(0,0.5), range(0,self.n))
    return seq
