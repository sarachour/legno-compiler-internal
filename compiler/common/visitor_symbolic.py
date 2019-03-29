import ops.op as op
import ops.nop as nop
import ops.op as ops
import numpy as np
import ops.interval as interval
from compiler.common.visitor import Visitor
from compiler.common.data_symbolic import SymbolicModel,SymbolicExprTable
import util.util as util

def wrap_coeff(coeff,expr):
  if coeff == 1.0:
    return expr
  else:
    return op.Mult(op.Const(coeff),expr)


def scaled_expr(block,config,output,expr):
  def recurse(e):
      return scaled_expr(block,config,output,e)

  comp_mode,scale_mode = config.comp_mode,config.scale_mode
  if expr.op == op.OpType.INTEG:
      ic_coeff = block.coeff(comp_mode,scale_mode,output,expr.ic_handle)
      deriv_coeff = block.coeff(comp_mode,scale_mode,output,expr.deriv_handle)
      stvar_coeff = block.coeff(comp_mode,scale_mode,output,expr.handle)
      return wrap_coeff(stvar_coeff,
                        op.Integ(\
                                  wrap_coeff(deriv_coeff,\
                                            recurse(expr.deriv)),
                                  wrap_coeff(ic_coeff,\
                                             recurse(expr.init_cond)),
                                  expr.handle
                        ))

  elif expr.op == op.OpType.MULT:
      return op.Mult(
          recurse(expr.arg1), recurse(expr.arg2)
      )
  else:
      return expr

def scaled_lut_dynamics_approx(config,output):
  terms = []
  for inp in config.expr(output).vars():
    inj = config.inject_var(inp)
    terms.append(op.Mult(op.Const(inj),op.Var(inp)))
  expr = op.mkadd(terms)
  return expr

def scaled_dynamics(block,config,output):
   comp_mode,scale_mode = config.comp_mode,config.scale_mode
   if config.has_expr(output):
     expr = config.expr(output,inject=True)
   else:
     expr = block.get_dynamics(comp_mode,output)

   scexpr = scaled_expr(block,config,output,expr)
   finalexpr = wrap_coeff(block.coeff(comp_mode,scale_mode,output), scexpr)
   return finalexpr

class SymbolicInferenceVisitor(Visitor):

  def __init__(self,circ,prop):
    Visitor.__init__(self,circ)
    self._gen_symtbl = SymbolicExprTable()
    self._in_symtbl = SymbolicExprTable()
    self._out_symtbl = SymbolicExprTable()
    self._prop = prop(self._in_symtbl,self._out_symtbl)
    self.initialize_generate_symbol_table()

  def initialize_generate_symbol_table(self):
    for block_name,loc,config in self.circ.instances():
      block = self.circ.board.block(block_name)
      for port in block.inputs:
        sig = nop.NSig(port,block=block_name,loc=loc)
        gen_model = SymbolicModel.from_expr(self._prop,sig,nop.mkzero())
        self.set_generate_model(block_name,loc,port,gen_model)
        self._gen_symtbl.put(block_name,loc,port,gen_model)

      for port in block.outputs:
        phys = config.physical(block,port)
        sig = nop.NSig(port,block=block_name,loc=loc)
        gen_expr = self.get_generate_expr(phys)
        gen_expr.bind_instance(block_name,loc)
        gen_model = SymbolicModel.from_expr(self._prop,sig,gen_expr)
        self.set_generate_model(block_name,loc,port,gen_model)
        self._gen_symtbl.put(block_name,loc,port,gen_model)


  def initialize_io_symbol_tables(self,first_time=False):
    if first_time:
      self._out_symtbl.clear()
      self._in_symtbl.clear()
      for block,loc,port,model in self._gen_symtbl.variables():
        self._in_symtbl.put(block,loc,port,model)

    else:
      self._in_symtbl.clear()
      for block,loc,port,model in self._out_symtbl.variables():
        self._in_symtbl.put(block,loc,port,model)
      self._out_symtbl.clear()


  def finalize(self):
    for block,loc,port,model in self._out_symtbl.variables():
      self.set_propagate_model(block,loc,port,model)

  def is_free(self,block_name,loc,port):
    return not self._out_symtbl.has(block_name,loc,port)


  def set_generate_model(self,block_name,loc,port,model):
    raise NotImplementedError

  def set_propagate_model(self,block_name,loc,port,model):
    raise NotImplementedError

  def get_generate_expr(self,stump):
    raise NotImplementedError

  def input_port(self,block_name,loc,port):
    Visitor.input_port(self,block_name,loc,port)
    circ = self._circ
    cfg = circ.config(block_name,loc)
    model = self._gen_symtbl.get(block_name,loc,port)
    for sblk,sloc,sport in \
      circ.get_conns_by_dest(block_name,loc,port):
      src_model = self._out_symtbl.get(sblk,sloc,sport)
      new_model = self._prop.plus(model,src_model)
      model = new_model

    model.set_signal(self._gen_symtbl.get(block_name,loc,port).signal)
    self._out_symtbl.put(block_name,loc,port,model)

  def output_port(self,block_name,loc,port):
    Visitor.output_port(self,block_name,loc,port)
    block = self._circ.board.block(block_name)
    config = self._circ.config(block_name,loc)
    sig = nop.NSig(port,block=block_name,loc=loc)
    expr = scaled_dynamics(block,config,port)
    # propagate dynamics
    self._prop.calculate_covariance = False
    prop_model = self._prop \
          .propagate_op(block_name,loc,port,expr)
    gen_model = self._gen_symtbl.get(block_name,loc,port)
    combo_model = self._prop.plus(prop_model,gen_model)
    combo_model.set_signal(self._gen_symtbl.get(block_name,loc,port).signal)

    self._out_symtbl.put(block_name,loc,port,combo_model)

  def compute(self):
    circ = self.circ
    for block_name,loc,config in circ.instances():
      block = circ.board.block(block_name)
      if block_name == 'integrator':
        for port in block.inputs:
          self.port(block_name,loc,port)

      else:
        for port in block.outputs:
          self.port(block_name,loc,port)

    for block_name,loc,config in circ.instances():
      if block_name == 'integrator':
        for port in block.outputs:
          self.port(block_name,loc,port)

    self.clear()

  def all(self,refinements=0):
    circ = self._circ
    # for completeness, visitor any ports we missed
    for refine_iter in range(0,refinements+1):
      print("REFINEMENT: <%d>" % refine_iter)
      self.initialize_io_symbol_tables(first_time=(refine_iter == 0))
      self.compute()

    self.finalize()
