import ops.op as op
import ops.nop as nop
import numpy as np
import ops.interval as interval
from compiler.common.visitor import Visitor
import zlib
import json
import binascii

class FreqCstrModel:
  def __init__(self):
    self._freqs = {}

  def decl(self,idx):
    if not idx in self._freqs:
      self._freqs[idx] = {}

  def add(self,idx,block_name,loc,port,freq_range):
    self.decl(idx)
    assert(not (block_name,loc,port) in self._freqs[idx])
    self._freqs[idx][(block_name,loc,port)] = freq_range

  def add_all(self,idx,cstrs):
    self.decl(idx)
    for (b,l,p),f in cstrs.items():
      assert(not (b,l,p) in self._freqs[idx])
      self._freqs[idx][(b,l,p)] = f

  def indices(self):
    return self._freqs.keys()

  def constraints(self,idx):
    return self._freqs[idx]

  @staticmethod
  def unify(cstrs1,cstrs2,overlapping):
    def update(isect,f):
      if f.spread > 0:
        return f if isect is None else isect.intersection(f)
      else:
        return isect

    cstrs = {}
    isect = None
    for (b,l,p),f1 in cstrs1.items():
      isect = update(isect,f1)
      if (b,l,p) in cstrs2:
        f2 = cstrs2[(b,l,p)]
        if not (f1.lower == f2.lower \
                and f1.upper == f2.upper):
          return None

        cstrs[(b,l,p)] = f1
      else:
        cstrs[(b,l,p)] = f1

    for (b,l,p),f1 in cstrs2.items():
      isect = update(isect,f1)
      if not (b,l,p) in cstrs1:
        cstrs[(b,l,p)] = f1

    if isect is None or (isect.spread > 0 or not overlapping):
      return cstrs
    else:
      return None


  def join(self,other,overlapping=False):
    for idx1 in self.indices():
      cstrs1 = self.constraints(idx1)
      for idx2 in other.indices():
        cstrs2 = other.constraints(idx2)
        cstrs = FreqCstrModel.unify(cstrs1,cstrs2,overlapping)
        if not cstrs is None:
          yield cstrs,idx1,idx2


  def to_json(self):
    obj = {}
    for idx,data in self._freqs.items():
      obj[str(idx)] = list(map(lambda args: (args[0],args[1].to_json()), \
                          data.items()))
    return obj

  @staticmethod
  def from_json(obj):
    cstrs = FreqCstrModel()
    for idx,data in obj.items():
      for ((b,l,p),fobj) in data:
        f = interval.Interval.from_json(fobj)
        cstrs.add(int(idx),b,l,p,f)

    return cstrs

class PiecewiseSymbolicModel:

  def __init__(self):
    self._model = {}
    self.cstrs = FreqCstrModel()

  def add_dist(self,mean,variance):
    assert(not mean is None)
    assert(not variance is None)
    assert(isinstance(mean,nop.NOp))
    assert(isinstance(variance,nop.NOp))
    idx = len(self._model)
    self._model[idx] = (mean,variance)
    self.cstrs.decl(idx)
    return idx

  def size(self):
    return len(self._model.keys())

  def add_expr(self,expr):
    return self.add_dist(expr.mean(),expr.variance())

  def model(self,idx):
    m,v = self._model[idx]
    return m,v

  def join(self,pwm):
    count = 0
    for cstrs,idx1,idx2 in self.cstrs.join(pwm.cstrs,overlapping=True):
      m1 = self.model(idx1)
      m2 = pwm.model(idx2)
      yield cstrs,self.model(idx1),pwm.model(idx2)
      count += 1

    #print("# pwfs: %d" % count)

  @staticmethod
  def from_json(hexstr):
    model = PiecewiseSymbolicModel()
    byte_obj = binascii.unhexlify(hexstr)
    comp_obj = zlib.decompress(byte_obj)
    obj = json.loads(str(comp_obj,'utf-8'))
    model.cstrs = FreqCstrModel.from_json(obj['cstrs'])
    for el in obj['data']:
      idx = int(el['index'])
      mean = nop.NOp.from_json(el['mean'])
      variance = nop.NOp.from_json(el['variance'])
      model._model[idx] = (mean,variance)
      model.cstrs.decl(idx)

    return model

  def is_posynomial(self):
    for m,v in self._model.values():
      if not m.is_posynomial() and not m.is_zero():
        return False
      if not v.is_posynomial() and not v.is_zero():
        return False
    return True

  def models(self):
    for idx,(mean,variance) in self._model.items():
      cstrs = self.cstrs.constraints(idx)
      yield cstrs,mean,variance

  def to_json(self):
    obj = {'data':[],'cstrs':self.cstrs.to_json()}
    for idx,(mean,variance) in self._model.items():
      obj['data'].append({
        'index':idx,
        'mean': mean.to_json(),
        'variance': variance.to_json()
      })
    byte_obj=json.dumps(obj).encode('utf-8')
    comp_obj = zlib.compress(byte_obj,3)
    return str(binascii.hexlify(comp_obj), 'utf-8')

  def __repr__(self):
    s = ""
    for idx,(m,v) in self._model.items():
      s += "=== %d ===\n" % idx
      s += "mean: %s\n" % m
      s += "vari: %s\n" % v
      s += "cstrs: %s\n" % self.cstrs.constraints(idx)

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
    model.add_expr(nop.mkzero())
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
    handle_model = PiecewiseSymbolicModel()
    handle_model.add_expr(
      nop.NRef(port,block_name,loc)
    )

    # compute generated noise
    gen_model = PiecewiseSymbolicModel()
    for freq_range,stump in phys.stumps():
      gen_expr = self.get_generate_expr(stump)
      gen_expr.bind_instance(block_name,loc)
      index = gen_model.add_expr(gen_expr)
      gen_model.cstrs.add(index,block_name, \
                          loc, phys.port,freq_range)

    if len(list(phys.stumps())) == 0:
      gen_model.add_expr(
        nop.mkzero()
      )

    # build a symbolic propagated model
    sym_prop_model = self._prop.plus(gen_model,handle_model)
    self.set_generate_model(block_name,loc,port,gen_model)
    self.set_propagate_model(block_name,loc,port,sym_prop_model)
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
    model.add_expr(nop.mkconst(abs(value)))
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
    model = PiecewiseSymbolicModel()
    for cstrs,u1,v1 in m.models():
      u = u1.exponent(0.5)
      v = v1.exponent(0.5)
      idx = model.add_dist(u,v)
      model.cstrs.add_all(idx,cstrs)

    return model

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

  def sin(self,m):
    # the smaller the magnitude of the signal
    # the higher the chance of a flip is.
    model = PiecewiseSymbolicModel()
    for cstrs,u1,v1 in m.models():
      u = u1
      v = v1
      idx = model.add_dist(u,v)
      model.cstrs.add_all(idx,cstrs)

    return model


  def sgn(self,m):
    # the smaller the magnitude of the signal
    # the higher the chance of a flip is.
    model = PiecewiseSymbolicModel()
    coeff = self.mksigexpr(self.expr.arg(0)).exponent(-1)
    for cstrs,u1,v1 in m.models():
      u = nop.mkmult([coeff,u1])
      v = nop.mkmult([coeff,v1])
      idx = model.add_dist(u,v)
      model.cstrs.add_all(idx,cstrs)

    return model

  def plus(self,m1,m2):
    model = PiecewiseSymbolicModel()
    for cstrs,(u1,v1),(u2,v2) in m1.join(m2):
      # compute mean
      u = nop.mkadd([u1,u2])
      # compute variance: cov <= sqrt(var1*var2)
      cov = nop.mkmult([nop.mkconst(2.0), \
                        self.covariance(v1,v2)])
      v = nop.mkadd([v1,v2,cov])
      idx = model.add_dist(u,v)
      model.cstrs.add_all(idx,cstrs)

    return model

  def mult(self,m1,m2):
    model = PiecewiseSymbolicModel()
    for cstrs,(u1,v1),(u2,v2) in m1.join(m2):
      # compute mean
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
      idx = model.add_dist(u,v)
      model.cstrs.add_all(idx,cstrs)

    return model
