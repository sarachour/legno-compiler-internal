import ops.nop as nop
from compiler.common.propagator_symbolic import ExpressionPropagator
from compiler.common.data_symbolic import SymbolicModel

class MathPropagator(ExpressionPropagator):

  def __init__(self,insymtbl,outsymtbl):
    ExpressionPropagator.__init__(self,insymtbl,outsymtbl)
    self.calculate_covariance = False

  def rv(self,rv):
    return SymbolicModel(nop.mkzero(),nop.mkconst(rv.mu),nop.mkconst(rv.sigma))

  def const(self,value):
    model = SymbolicModel(nop.mkconst(value), nop.mkzero(), nop.mkzero())
    assert(model.is_posynomial() or value == 0.0)
    return model

  def covariance(self,v1,v2):
    # cov < sqrt(v1*v2)
    if self.calculate_covariance:
      # b*A^(b-1)*variance
      expr = nop.mkmult([v1.exponent(0.5),v2.exponent(0.5)])
      return expr
    else:
      return nop.mkzero()

  def integ(self,deriv,ic):
    return deriv

  def abs(self,m):
    u,v = m.mean, m.variance
    s = m.signal
    sig = nop.mkmult([s,s]).exponent(0.5)
    ures = nop.mkmult([u,u]).exponent(0.5)
    vres = nop.mkmult([v,v]).exponent(0.5)
    return SymbolicModel(sig,ures,vres)

  def sqrt(self,m):
    u,v = m.mean, m.variance
    s = m.signal.exponent(0.5)
    ur = u.exponent(0.5)
    vr = v.exponent(0.5)
    return SymbolicModel(s,ur,vr)

  def mksigexpr(self,expr):
    block,loc,port = self.place
    if expr.op == op.OpType.VAR:
      return nop.NSig(expr.name,
                      power=1.0,
                      block=block,
                      loc=loc)
    elif expr.op == op.OpType.CONST:
      return nop.NConstRV(expr.value,0)
    elif expr.op == op.OpType.MULT:
      arg1 = self.mksigexpr(expr.arg1)
      arg2 = self.mksigexpr(expr.arg2)
      return nop.mkmult([arg1,arg2])
    else:
      raise NotImplementedError("mksigexpr: not implemented: %s" % expr)

  def cos(self,m):
    # the smaller the magnitude of the signal
    # the higher the chance of a flip is.
    return self.sin(m)


  def sin(self,m):
    # the smaller the magnitude of the signal
    # the higher the chance of a flip is.
    u,v = m.mean, m.variance
    # sensitivity analysis
    newu = nop.mkmult([nop.NConstRV(0.5,0),u])
    newv = nop.mkmult([nop.NConstRV(0.5,0),v])
    return SymbolicModel(nop.NConstRV(1.0,0.0),newu,newv)


  def sgn(self,m):
    # the smaller the magnitude of the signal
    # the higher the chance of a flip is.
    u,v = m.mean,m.variance
    return SymbolicModel(nop.NConstRV(1.0,0.0),
                         nop.NConstRV(0.0,0.0),
                         nop.NConstRV(0.1,0.0))

  def plus(self,m1,m2):
    s1,u1,v1 = m1.signal,m1.mean,m1.variance
    s2,u2,v2 = m2.signal,m2.mean,m2.variance
    s = nop.mkadd([s1,s2])
    u = nop.mkadd([u1,u2])
    # compute variance: cov <= sqrt(var1*var2)
    cov = self.covariance(v1,v2)
    #cov = nop.mkmult([v1,v2])

    v = nop.mkadd([v1,v2,cov])
    return SymbolicModel(s,u,v)

  def mult(self,m1,m2):
    s1,u1,v1 = m1.signal,m1.mean,m1.variance
    s2,u2,v2 = m2.signal,m2.mean,m2.variance
    x1 = nop.mkadd([u1,s1])
    x2 = nop.mkadd([u2,s2])
    s = nop.mkmult([s1,s2])
    u = nop.mkadd([
      nop.mkmult([u1,s2]),
      nop.mkmult([s1,u2]),
      nop.mkmult([u1,u2])
    ])
    # compute variance
    #cov = nop.mkmult([nop.mkconst(2.0), \
    #                            s1,s2, \
    #                            v1,v2])
    #cov = nop.mkmult([nop.mkconst(2.0), \
    #                  self.covariance(v1,v2), \
    #                  s1,s2])
    t1 = nop.mkmult([x1,x1,v2])
    t2 = nop.mkmult([x2,x2,v1])
    v = nop.mkadd([
      t1,t2
    ])
    return SymbolicModel(s,u,v)
