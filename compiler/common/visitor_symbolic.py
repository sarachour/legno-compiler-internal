import ops.op as op
import ops.nop as nop
import ops.op as ops
import numpy as np
import ops.interval as interval
from compiler.common.visitor import Visitor
import zlib
import json
import binascii

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
     expr = config.expr(output)
   else:
     expr = block.get_dynamics(comp_mode,output)
   scexpr = scaled_expr(block,config,output,expr)
   return wrap_coeff(block.coeff(comp_mode,scale_mode,output), scexpr)

class SymbolicModel:

  def __init__(self,mean,variance):
    self._mean = mean
    self._variance = variance

  @staticmethod
  def from_expr(expr):
    return SymbolicModel(expr.mean(),expr.variance())

  @property
  def mean(self):
    return self._mean

  @property
  def variance(self):
    return self._variance

  def join(self,pwm):
    yield self,pwm


  def is_posynomial(self):
    if not self.mean.is_posynomial() and not m.is_zero():
      return False
    if not self.variance.is_posynomial() and not v.is_zero():
      return False
    return True


  @staticmethod
  def from_json(hexstr):
    byte_obj = binascii.unhexlify(hexstr)
    comp_obj = zlib.decompress(byte_obj)
    obj = json.loads(str(comp_obj,'utf-8'))
    mean = nop.NOp.from_json(obj['mean'])
    variance = nop.NOp.from_json(obj['variance'])
    model = SymbolicModel(mean,variance)
    return model

  def to_json(self):
    obj= {
      'mean': self._mean.to_json(),
      'variance': self._variance.to_json()
    }
    byte_obj=json.dumps(obj).encode('utf-8')
    comp_obj = zlib.compress(byte_obj,3)
    return str(binascii.hexlify(comp_obj), 'utf-8')

  def __repr__(self):
    s = "mean: %s\n" % self._mean
    s += "vari: %s\n" % self._variance
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


  def propagate(self,block_name,loc,port,expr):
    def recurse(e):
      return self.propagate(block_name,loc,port,e)

    self.block = block_name
    self.loc = loc
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
      model = self._env.get_propagate_model(block_name, \
                                       loc, \
                                       expr.name)
      return model

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

    model = SymbolicModel.from_expr(nop.mkzero())
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

    # build a symbolic handle
    handle_model = SymbolicModel.from_expr(
      nop.NRef(port,block_name,loc)
    )
    # compute generated noise
    gen_expr = self.get_generate_expr(phys)
    gen_expr.bind_instance(block_name,loc)
    gen_model = SymbolicModel.from_expr(gen_expr)

    # build a symbolic propagated model
    sym_prop_model = self._prop.plus(gen_model,handle_model)
    self.set_generate_model(block_name,loc,port,gen_model)
    self.set_propagate_model(block_name,loc,port,sym_prop_model)
    Visitor.output_port(self,block_name,loc,port)

    # compute propagated noise
    expr = scaled_dynamics(block,config,port)
    prop_model = self._prop \
          .propagate(block_name,loc,port,expr)
    combo_model = self._prop.plus(prop_model,gen_model)
    self.set_propagate_model(block_name,loc,port,combo_model)

class MathPropagator(ExpressionPropagator):

  def __init__(self,env):
    ExpressionPropagator.__init__(self,env)

  def const(self,value):
    model = SymbolicModel.from_expr(nop.mkconst(abs(value)))
    assert(model.is_posynomial() or value == 0.0)
    return model

  def covariance(self,v1,v2,correlated=False):
    # cov < sqrt(v1*v2)
    if correlated:
      return nop.mkmult([v1.sqrt(),v2.sqrt()])
    else:
      return nop.mkzero()

  def integ(self,deriv,ic):
    assert(deriv.is_posynomial())
    return deriv

  def abs(self,m):
    return m

  def sqrt(self,m):
    u,v = m.mean, m.variance
    ur = u.exponent(0.5)
    vr = v.exponent(0.5)
    return SymbolicModel(ur,vr)

  def mksigexpr(self,expr):
    if expr.op == op.OpType.VAR:
      return nop.NSig(expr.name,
                      power=1.0,
                      block=self.block,
                      loc=self.loc)
    elif expr.op == op.OpType.CONST:
      return nop.NConstRV(expr.value,0)
    elif expr.op == op.OpType.MULT:
      arg1 = self.mksigexpr(expr.arg1)
      arg2 = self.mksigexpr(expr.arg2)
      return nop.NMult([arg1,arg2])
    else:
      raise NotImplementedError("mksigexpr: not implemented: %s" % expr)

  def cos(self,m):
    # the smaller the magnitude of the signal
    # the higher the chance of a flip is.
    u,v = m.mean, m.variance
    return SymbolicModel(u,v)


  def sin(self,m):
    # the smaller the magnitude of the signal
    # the higher the chance of a flip is.
    u,v = m.mean, m.variance
    return SymbolicModel(u,v)


  def sgn(self,m):
    # the smaller the magnitude of the signal
    # the higher the chance of a flip is.
    u,v = m.mean,m.variance
    coeff = self.mksigexpr(self.expr.arg(0)).exponent(-1)
    ur = nop.mkmult([coeff,u])
    vr = nop.mkmult([coeff,v])
    return SymbolicModel(ur,vr)

  def plus(self,m1,m2):
    u1,v1 = m1.mean,m1.variance
    u2,v2 = m2.mean,m2.variance
    u = nop.mkadd([u1,u2])
    # compute variance: cov <= sqrt(var1*var2)
    cov = nop.mkmult([nop.mkconst(2.0), \
                      self.covariance(v1,v2)])
    v = nop.mkadd([v1,v2,cov])
    return SymbolicModel(u,v)

  def mult(self,m1,m2):
    u1,v1 = m1.mean,m1.variance
    u2,v2 = m2.mean,m2.variance
    u = nop.mkmult([u1,u2])
    # compute variance
    cov = nop.mkmult([nop.mkconst(2.0), \
                      self.covariance(v1,v2), \
                      u1,u2])
    t1 = nop.mkmult([u1,u1,v2])
    t2 = nop.mkmult([u2,u2,v1])
    v = nop.mkadd([
      t1,t2,cov
    ])
    return SymbolicModel(u,v)

