from enum import Enum
import random
from scipy.io import arff

class Category(Enum):
  ANOMALY = "anomaly"
  NORMAL = "normal"

  @staticmethod
  def from_code(x):
    if x == Category.ANOMALY.to_code():
      return Category.ANOMALY
    elif x == Category.NORMAL.to_code():
      return Category.NORMAL
    else:
      raise Exception("unknown code <%f>" % x)

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
    self.size = self.n*self.num_tests

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


  def generate_train_dataset(self):
    for i in range(self.num_tests):
      if i % 2 == 0:
        yield self.get_anomaly()
      else:
        yield self.get_normal()

  def generate_test_dataset(self):
    for ds in self.generate_train_dataset():
      yield ds

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

class DataBackedRNNAnomaly(RNNAnomaly):

  def __init__(self,train,test,anomaly,normal,npts):
    RNNAnomaly.__init__(self,-1,-1)
    ns,self.train = self.load_data(train,anomaly,normal,npts)
    self.size = sum(ns)
    _,self.test = self.load_data(test,anomaly,normal,npts)

  def load_data(self,filename,anomaly,normal,npts):
    data,meta = arff.loadarff(filename)
    classification = data['target']
    xs = {}
    ns = []
    for i in range(0,len(classification)):
      x = list(map(lambda j: data['att%d' % j][i],range(1,npts+1)))
      y = float(data['target'][i])
      if y == anomaly:
        ycat = Category.ANOMALY
      elif y == normal:
        ycat = Category.NORMAL
      else:
        raise Exception("unknown category")

      if not ycat in xs:
        xs[ycat] = []

      xs[ycat].append(x)
      ns.append(len(x))

    return ns,xs

    self.num_tests = len(self.xs)
    self.size = sum(self.ns)

  def generate_anomaly(self):
    idx = random.randint(0,len(self.train[Category.ANOMALY])-1)
    return self.train[Category.ANOMALY][idx]

  def generate_normal(self):
    idx = random.randint(0,len(self.train[Category.NORMAL])-1)
    return self.train[Category.NORMAL][idx]

  def generate_test_dataset(self):
    for cat,data in self.test.items():
      for seq in data:
        yield seq,cat.to_code()


  def generate_train_dataset(self):
    for cat,data in self.train.items():
      for seq in data:
        yield seq,cat.to_code()

class EarthquakeRNNAnomaly(DataBackedRNNAnomaly):

  def __init__(self,n):
    train = "datasets/EARTHQUAKES_TRAIN.arff"
    test = "datasets/EARTHQUAKES_TEST.arff"
    DataBackedRNNAnomaly.__init__(self,test,train,1,0,512)

class HeartRNNAnomaly(DataBackedRNNAnomaly):


  def __init__(self,n):
    train = "datasets/ECG200_TRAIN.arff"
    test = "datasets/ECG200_TEST.arff"
    DataBackedRNNAnomaly.__init__(self,test,train,-1.0,1.0,96)

class FordRNNAnomaly(DataBackedRNNAnomaly):


  def __init__(self,n):
    train = "datasets/FordA_TRAIN.arff"
    test = "datasets/FordA_TEST.arff"
    FordRNNAnomaly.__init__(self,test,train,-1.0,1.0,96)
