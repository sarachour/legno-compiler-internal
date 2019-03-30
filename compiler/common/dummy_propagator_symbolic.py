from compiler.common.propagator_symbolic import ExpressionPropagator
from compiler.common.data_symbolic import SymbolicModel
import ops.nop as nop
import ops.op as op


class ZeroPropagator(ExpressionPropagator):

  def __init__(self,insymtbl,outsymtbl):
    self._in = insymtbl
    self._out = outsymtbl

  def propagate_nop(self,expr):
    return SymbolicModel(nop.mkzero(),nop.mkzero(),nop.mkzero())

  def propagate_op(self,block,loc,port,expr):
    return SymbolicModel(nop.mkzero(),nop.mkzero(),nop.mkzero())

  def plus(self,m1,m2):
    s1,u1,v1 = m1.signal,m1.mean,m1.variance
    s2,u2,v2 = m2.signal,m2.mean,m2.variance
    s = nop.mkadd([s1,s2])
    u = nop.mkadd([u1,u2])
    v = nop.mkadd([v1,v2])
    return SymbolicModel(s,u,v)

