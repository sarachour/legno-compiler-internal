import ops.op as op
import ops.nop as nop
import ops.op as ops
import numpy as np
import ops.interval as interval
from compiler.common.visitor import Visitor
import util.util as util

def wrap_coeff(coeff,expr):
  if coeff == 1.0:
    return expr
  else:
    return ops.Mult(ops.Const(coeff),expr)


def scaled_expr(block,config,output,expr):
  def recurse(e):
      return scaled_expr(block,config,output,e)

  comp_mode,scale_mode = config.comp_mode,config.scale_mode
  if expr.op == ops.OpType.INTEG:
      ic_coeff = block.coeff(comp_mode,scale_mode,output,expr.ic_handle)
      deriv_coeff = block.coeff(comp_mode,scale_mode,output,expr.deriv_handle)
      stvar_coeff = block.coeff(comp_mode,scale_mode,output,expr.handle)
      return wrap_coeff(stvar_coeff,
                        ops.Integ(\
                                  wrap_coeff(deriv_coeff,\
                                            recurse(expr.deriv)),
                                  wrap_coeff(ic_coeff,\
                                             recurse(expr.init_cond)),
                                  expr.handle
                        ))

  elif expr.op == ops.OpType.MULT:
      return ops.Mult(
          recurse(expr.arg1), recurse(expr.arg2)
      )
  else:
      return expr

def scaled_dynamics(block,config,output):
   comp_mode,scale_mode = config.comp_mode,config.scale_mode
   if config.has_expr(output):
     expr = config.expr(output,inject=False)
   else:
     expr = block.get_dynamics(comp_mode,output)

   scexpr = scaled_expr(block,config,output,expr)
   return wrap_coeff(block.coeff(comp_mode,scale_mode,output), scexpr)

class SymbolicModel:
  IGNORE_CHECKS = True

  def __init__(self,signal,mean,variance):
    self._signal = signal
    self._mean = mean
    self._variance = variance

  @staticmethod
  def from_expr(sigexpr,expr):
    prop = BaseMathPropagator()
    sigm = prop.propagate_nop(sigexpr)
    phym = prop.propagate_nop(expr)
    newm = SymbolicModel(sigm.mean,phym.mean,phym.variance)
    return newm

  @property
  def mean(self):
    return self._mean

  @property
  def signal(self):
    return self._signal

  @property
  def variance(self):
    return self._variance

  def join(self,pwm):
    yield self,pwm


  def is_posynomial(self):
    if SymbolicModel.IGNORE_CHECKS:
      return True

    if not self.mean.is_posynomial() and not m.is_zero():
      return False
    if not self.variance.is_posynomial() and not v.is_zero():
      return False
    return True


  @staticmethod
  def from_json(hexstr):
    obj = util.decompress_json(hexstr)
    signal = nop.NOp.from_json(obj['signal'])
    mean = nop.NOp.from_json(obj['mean'])
    variance = nop.NOp.from_json(obj['variance'])
    model = SymbolicModel(signal,mean,variance)
    return model

  def to_json(self):
    obj= {
      'signal': self._signal.to_json(),
      'mean': self._mean.to_json(),
      'variance': self._variance.to_json()
    }
    hexstr = util.compress_json(obj)
    return hexstr

  def __repr__(self):
    s = "sig: %s\n" % self._signal
    s += "mean: %s\n" % self._mean
    s += "vari: %s\n" % self._variance
    return s

class ExpressionPropagator:

  def __init__(self):
    pass

  def mult(self,m1,m2):
    raise NotImplementedError

  def rv(self,c):
    raise NotImplementedError

  def const(self,c):
    raise NotImplementedError

  def plus(self,m1,m2):
    raise NotImplementedError

  def integ(self,m1,m2):
    raise NotImplementedError

  def sqrt(self,m):
    raise NotImplementedError

  def abs(self,m):
    raise NotImplementedError

  def cos(self,m):
    raise NotImplementedError

  def sin(self,m):
    raise NotImplementedError

  def sgn(self,m):
    raise NotImplementedError

  def nop_var(self,v):
    raise NotImplementedError


  def op_var(self,v):
    raise NotImplementedError

  def propagate_nop(self,expr):
    def recurse(e):
      return self.propagate_nop(e)

    if expr.op == nop.NOpType.SIG:
      return self.nop_var(expr)
    elif expr.op == nop.NOpType.FREQ:
      return self.nop_var(expr)
    elif expr.op == nop.NOpType.REF:
      return self.nop_var(expr)
    elif expr.op == nop.NOpType.CONST_RV:
      return self.rv(expr)
    elif expr.op == nop.NOpType.ADD:
      sum_v= recurse(nop.mkzero())
      for term in expr.terms():
        term_v = recurse(term)
        sum_v = self.plus(sum_v,term_v)
      return sum_v
    elif expr.op == nop.NOpType.MULT:
      sum_v= recurse(nop.mkone())
      for term in expr.terms():
        term_v = recurse(term)
        sum_v = self.mult(sum_v,term_v)
      return sum_v


    else:
      raise Exception("unimpl: %s" % expr)

  def propagate_op(self,block,loc,port,expr):
    def recurse(e):
      return self.propagate_op(block,loc,port,e)

    self.place = (block,loc,port)
    if expr.op == op.OpType.INTEG:
      m1 = recurse(expr.deriv)
      m2 = recurse(expr.init_cond)
      self.expr = expr
      return self.integ(m1,m2)

    elif expr.op == op.OpType.MULT:
      m1 = recurse(expr.arg1)
      m2 = recurse(expr.arg2)
      self.expr = expr
      return self.mult(m1,m2)

    elif expr.op == op.OpType.VAR:
      return self.op_var(expr.name)

    elif expr.op == op.OpType.CONST:
      self.expr = expr
      return self.const(expr.value)

    elif expr.op == op.OpType.SGN:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      return self.sgn(m1)

    elif expr.op == op.OpType.SQRT:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      return self.sqrt(m1)

    elif expr.op == op.OpType.ABS:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      return self.abs(m1)


    elif expr.op == op.OpType.COS:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      return self.cos(m1)


    elif expr.op == op.OpType.SIN:
      m1 = recurse(expr.arg(0))
      self.expr = expr
      return self.sin(m1)

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

    cfg = circ.config(block_name,loc)
    if cfg.has_dac(port):
      value = cfg.dac(port)
      model = SymbolicModel.from_expr(nop.NSig(port,block=block_name,loc=loc),nop.mkzero())
    else:
      model = SymbolicModel.from_expr(nop.mkzero(),nop.mkzero())

    for sblk,sloc,sport in \
      circ.get_conns_by_dest(block_name,loc,port):
      assert(not self.get_propagate_model(sblk,sloc,sport) is None)
      src_model = self.get_propagate_model(sblk,sloc,sport)
      new_model = self._prop.plus(model,src_model)
      model = new_model

    self.set_propagate_model(block_name,loc,port,model)

  def output_port(self,block_name,loc,port):
    block = self._circ.board.block(block_name)
    config = self._circ.config(block_name,loc)
    phys = config.physical(block,port)

    sig = nop.NSig(port,block=block_name,loc=loc)
    # build a symbolic handle
    handle_model = SymbolicModel.from_expr(
      sig, nop.NRef(port,1.0,block_name,loc)
    )
    # compute generated noise
    gen_expr = self.get_generate_expr(phys)
    gen_expr.bind_instance(block_name,loc)
    gen_model = SymbolicModel.from_expr(nop.mkzero(),gen_expr)
    # build a symbolic propagated model
    sym_prop_model = self._prop.plus(gen_model,handle_model)
    self.set_generate_model(block_name,loc,port,gen_model)
    self.set_propagate_model(block_name,loc,port,sym_prop_model)
    # visit
    Visitor.output_port(self,block_name,loc,port)

    # compute propagated noise
    expr = scaled_dynamics(block,config,port)
    prop_model = self._prop \
          .propagate_op(block_name,loc,port,expr)
    combo_model = self._prop.plus(prop_model,gen_model)
    self.set_propagate_model(block_name,loc,port,combo_model)

  def toplevel(self):
    circ = self._circ
    for handle,block_name,loc in circ.board.handles():
      if circ.in_use(block_name,loc):
        config = circ.config(block_name,loc)
        for port,label,kind in config.labels():
          self.port(block_name,loc,port)


  def all(self):
    circ = self._circ
    for block_name,loc,config in circ.instances():
      if not block_name == 'integrator':
        continue
      self.block(block_name,loc)

    self.toplevel()
    # for completeness, visitor any ports we missed
    for block_name,loc,config in circ.instances():
      block = circ.board.block(block_name)
      for port in block.outputs:
        if not self.visited(block_name,loc,port):
          self.port(block_name,loc,port)

class BaseMathPropagator(ExpressionPropagator):

  def __init__(self):
    ExpressionPropagator.__init__(self)

  def nop_var(self,v):
    return SymbolicModel(nop.mkzero(),v,nop.mkzero())

  def rv(self,rv):
    return SymbolicModel(nop.mkzero(),nop.mkconst(rv.mu),nop.mkconst(rv.sigma))

  def const(self,value):
    model = SymbolicModel(nop.mkconst(value), nop.mkzero(), nop.mkzero())
    assert(model.is_posynomial() or value == 0.0)
    return model

  def covariance(self,v1,v2,correlated=False):
    # cov < sqrt(v1*v2)
    if correlated:
      return nop.mkmult([v1.sqrt(),v2.sqrt()])
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
                         nop.NConstRV(1.0,0.0))

  def plus(self,m1,m2):
    s1,u1,v1 = m1.signal,m1.mean,m1.variance
    s2,u2,v2 = m2.signal,m2.mean,m2.variance
    s = nop.mkadd([s1,s2])
    u = nop.mkadd([u1,u2])
    # compute variance: cov <= sqrt(var1*var2)
    cov = self.covariance(v1,v2)
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
    cov = nop.mkmult([nop.mkconst(2.0), \
                      self.covariance(v1,v2), \
                      x1,x2])
    t1 = nop.mkmult([x1,x1,v2])
    t2 = nop.mkmult([x2,x2,v1])
    v = nop.mkadd([
      t1,t2,cov
    ])
    return SymbolicModel(s,u,v)


class MathPropagator(BaseMathPropagator):

  def __init__(self,env):
    BaseMathPropagator.__init__(self)
    self._env = env

  def op_var(self,name):
    block,loc,_ = self.place
    model = self._env.get_propagate_model(block, \
                                          loc, \
                                          name)

    return model
