import ops.op as op
import ops.nop as nop
import numpy as np
import ops.interval as interval
from compiler.common.visitor import Visitor

class PiecewiseSymbolicModel:

  def __init__(self):
    self._intervals = []
    self._model = {}

  def add(self,freq_range,expr):
    for ival in self._intervals:
      assert(ival.intersection(freq_range) == 0.0)

    idx = len(self._intervals)
    self._intervals.append(freq_range)
    self._model[idx] = (expr.mean(),expr.variance())

  def intervals(self):
    for ival in self._intervals:
      yield ival

  def join(self,other):
    is1 = list(self.intervals())
    is2 = list(other.intervals())
    print(is1)
    print(is2)
    input()

class SymbolicEnvironment:

  def __init__(self):
    self._syms = {}

  def has(self,block_name,loc,port):
    return (block_name,loc,port) in self._syms

  def make(self,block_name,loc,port):
    print('make %s[%s].%s' % (block_name,loc,port))
    assert(not self.has(block_name,loc,port))
    self._syms[(block_name,loc,port)] = \
                                PiecewiseSymbolicModel()
    return self._syms[(block_name,loc,port)]

  def get(self,block_name,loc,port):
    if not (self.has(block_name,loc,port)):
      raise Exception("no symbolic model: %s[%s].%s" % \
                      (block_name,loc,port))
    return self._syms[(block_name,loc,port)]

class ExpressionPropagater:

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

    print(expr)
    if expr.op == op.OpType.INTEG:
      m1 = recurse(expr.deriv)
      m2 = recurse(expr.init_cond)
      return self.integ(m1,m2)

    elif expr.op == op.OpType.MULT:
      m1 = recurse(expr.arg1)
      m2 = recurse(expr.arg2)
      return self.mult(m1,m2)

    elif expr.op == op.OpType.VAR:
      model = self._env.get(block_name,loc,expr.name)
      return model

    elif expr.op == op.OpType.CONST:
      return self.const(expr.value)

    else:
      raise Exception("unimplemented: %s" % (expr))


class SymbolicInferenceVisitor(Visitor):

  def __init__(self,circ,prop):
    Visitor.__init__(self,circ)
    self._env = SymbolicEnvironment()
    self._prop = prop(self._env)

  def is_free(self,block_name,loc,port):
    return not self._env.has(block_name,loc,port)

  def get_expr(self,stump):
    raise NotImplementedError

  def input_port(self,block_name,loc,port):
    Visitor.input_port(self,block_name,loc,port)
    circ = self._circ
    model = self._env.make(block_name,loc,port)
    model.add(
      interval.Interval.type_infer(None,None),
      nop.NZero()
    )
    for sblk,sloc,sport in \
      circ.get_conns_by_dest(block_name,loc,port):
      assert(self._env.has(sblk,sloc,sport))
      src_model = self._env.get(sblk,sloc,sport)
      model = self._prop.plus(model,src_model)


  def output_port(self,block_name,loc,port):
    block = self._circ.board.block(block_name)
    config = self._circ.config(block_name,loc)
    phys = config.physical(block,port)

    # compute generated noise
    model = self._env.make(block_name,loc,port)
    for freq_range,stump in phys.stumps():
      gen_expr = self.get_expr(stump)
      model.add(freq_range,gen_expr)

    Visitor.output_port(self,block_name,loc,port)

    # compute propagated noise
    expr = config.dynamics(block,port)
    prop_model = self._prop \
          .propagate(block_name,loc,port,expr)

    input("output")
    raise NotImplementedError

class PropNoisePropagater(ExpressionPropagater):

  def __init__(self,env):
    ExpressionPropagater.__init__(self,env)

  def const(self,value):
    model = PiecewiseSymbolicModel()
    freq_range = interval.Interval.type_infer(None,None)
    model.add(freq_range,nop.NConstVal(value))
    return model

  def mult(self,m1,m2):
    for ival,(u1,v1),(u2,v2) in m1.join(m2):
      print(ival)
      print(e1)
      print(e2)
      print('------')

    input()

class PropNoiseVisitor(SymbolicInferenceVisitor):

  def __init__(self,circ):
    SymbolicInferenceVisitor.__init__(self,circ,\
                                      PropNoisePropagater)

  def get_expr(self,stump):
    return stump.noise

def compute(circ):
  inf = PropNoiseVisitor(circ)
  inf.all()
  input("done")
