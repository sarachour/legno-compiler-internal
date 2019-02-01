import ops.op as op
import ops.nop as nop
import numpy as np
import ops.interval as interval
from compiler.common.visitor import Visitor


class PiecewiseSymbolicModel:

  def __init__(self):
    self._intervals = []
    self._model = {}

  def add_dist(self,freq_range,mean,variance):
    for ival in self._intervals:
      assert(ival.intersection(freq_range).spread == 0.0)

    idx = len(self._intervals)
    if idx > 0:
      self._intervals[idx-1].upper == freq_range.lower

    self._intervals.append(freq_range)
    self._model[idx] = (mean,variance)

  def add_expr(self,freq_range,expr):
    self.add_dist(freq_range,expr.mean(),expr.variance())

  def intervals(self):
    for ival in self._intervals:
      yield ival

  def join(self,other):
    is1 = list(self.intervals())
    is2 = list(other.intervals())
    assert(len(is1) >= 1)
    assert(len(is2) >= 1)
    i,j = 0,0
    while i < len(is1) and j < len(is2):
      ival1, ival2 = is1[i], is2[j]
      yield ival1.intersection(ival2),\
        self._model[i],other._model[j]

      if ival1.upper == ival2.upper:
        i += 1
        j += 1
      elif ival1.upper < ival2.upper:
        i += 1
      else:
        j += 1

  def __repr__(self):
    s = ""
    for idx,ival in enumerate(self._intervals):
      m,v = self._model[idx]
      s += "=== %s ===\n" % ival
      s += "mean: %s\n" % m
      s += "vari: %s\n" % v

    return s

class ExpressionPropagator:

  def __init__(self,env):
    self._env = env

  def mult(self,m1,m2):
    raise NotImplementedError

  def const(self,c):
    raise NotImplementedError

  def plus(self,m1,m2):
    raise NotImplementedError

  def integ(self,m1,m2):
    raise NotImplementedError

  def propagate(self,block_name,loc,port,expr):
    def recurse(e):
      return self.propagate(block_name,loc,port,e)

    if expr.op == op.OpType.INTEG:
      m1 = recurse(expr.deriv)
      m2 = recurse(expr.init_cond)
      return self.integ(m1,m2)

    elif expr.op == op.OpType.MULT:
      m1 = recurse(expr.arg1)
      m2 = recurse(expr.arg2)
      return self.mult(m1,m2)

    elif expr.op == op.OpType.VAR:
      model = self._env.get_propagate_model(block_name, \
                                       loc, \
                                       expr.name)
      return model

    elif expr.op == op.OpType.CONST:
      return self.const(expr.value)

    else:
      raise Exception("unimplemented: %s" % (expr))


class SymbolicInferenceVisitor(Visitor):

  def __init__(self,circ,prop):
    Visitor.__init__(self,circ)
    self._prop = prop(self)

  def is_free(self,block_name,loc,port):
    g = self.get_generate_model(block_name,loc,port)
    p = self.get_propagate_model(block_name,loc,port)
    return g is None or p is None

  def get_propagate_model(self,block_name,loc,port):
    raise NotImplementedError

  def get_generate_model(self,block_name,loc,port):
    raise NotImplementedError
    config = self.circ.config(block_name,loc,port)
    gen = config.generated_noise(block_name,loc,port)
    prop = config.propagated_noise(block_name,loc,port)
    return gen,prop

  def set_generate_model(self,block_name,loc,port,model):
    raise NotImplementedError

  def set_propagate_model(self,block_name,loc,port,model):
    raise NotImplementedError

  def get_generate_expr(self,stump):
    raise NotImplementedError

  def input_port(self,block_name,loc,port):
    Visitor.input_port(self,block_name,loc,port)
    circ = self._circ

    if not self.get_propagate_model(block_name,loc,port) is None:
      return

    model = PiecewiseSymbolicModel()
    model.add_expr(
      interval.Interval.type_infer(0,None),
      nop.NZero()
    )
    for sblk,sloc,sport in \
      circ.get_conns_by_dest(block_name,loc,port):
      assert(not self.get_propagate_model(sblk,sloc,sport) is None)
      src_model = self.get_propagate_model(sblk,sloc,sport)
      model = self._prop.plus(model,src_model)

    self.set_propagate_model(block_name,loc,port,model)

  def output_port(self,block_name,loc,port):
    block = self._circ.board.block(block_name)
    config = self._circ.config(block_name,loc)
    phys = config.physical(block,port)

    # compute generated noise
    gen_model = PiecewiseSymbolicModel()
    for freq_range,stump in phys.stumps():
      gen_expr = self.get_generate_expr(stump)
      gen_model.add_expr(freq_range,gen_expr)
    if len(list(phys.stumps())) == 0:
      gen_model.add_expr(
        interval.Interval.type_infer(0,None),
        nop.NZero()
      )
    self.set_generate_model(block_name,loc,port,gen_model)
    self.set_propagate_model(block_name,loc,port,gen_model)
    Visitor.output_port(self,block_name,loc,port)

    # compute propagated noise
    expr = config.dynamics(block,port)
    prop_model = self._prop \
          .propagate(block_name,loc,port,expr)

    combo_model = self._prop.plus(prop_model,gen_model)
    self.set_propagate_model(block_name,loc,port,combo_model)

class MathPropagator(ExpressionPropagator):

  def __init__(self,env):
    ExpressionPropagator.__init__(self,env)

  def const(self,value):
    model = PiecewiseSymbolicModel()
    freq_range = interval.Interval.type_infer(0,None)
    model.add_expr(freq_range,nop.NConstVal(value))
    return model

  def covariance(self,v1,v2):
    # cov < sqrt(v1*v2)
    return nop.mkmult([v1.sqrt(),v2.sqrt()])

  def integ(self,deriv,ic):
    return deriv

  def plus(self,m1,m2):
    model = PiecewiseSymbolicModel()
    for ival,(u1,v1),(u2,v2) in m1.join(m2):
      # compute mean
      u = nop.mkadd([u1,u2])
      # compute variance: cov <= sqrt(var1*var2)
      cov = nop.mkmult([nop.NConstVal(2.0), \
                        self.covariance(v1,v2)])
      v = nop.mkadd([v1,v2,cov])
      model.add_dist(ival,u,v)

    return model

  def mult(self,m1,m2):
    model = PiecewiseSymbolicModel()
    for ival,(u1,v1),(u2,v2) in m1.join(m2):
      # compute mean
      u = nop.mkmult([u1,u2])
      # compute variance
      cov = nop.mkmult([nop.NConstVal(2.0), \
                        self.covariance(v1,v2), \
                        u1,u2])
      t1 = nop.mkmult([u1.square(),v2])
      t2 = nop.mkmult([u2.square(),v1])
      v = nop.mkadd([
        t1,t2,cov
      ])
      model.add_dist(ival,u,v)

    return model
