from compiler.common.visitor import ForwardVisitor
import chip.props as props
import ops.op as ops
import ops.nop as nop
import compiler.common.base_propagator_symbolic as propagate
import compiler.common.data_symbolic as symdata
import math
from ops.interval import Interval, IRange, IValue
from chip.model import ModelDB, PortModel,get_variance

# find the most expensive input
class PropCostVisitor(ForwardVisitor):

  def __init__(self,circ,prop_cost=True,ideal=False):
    ForwardVisitor.__init__(self,circ)
    self._db = ModelDB()
    self._prop_cost = prop_cost
    self._ideal = ideal
    self._no_model = []

  def is_free(self,block_name,loc,port):
    config = self._circ.config(block_name,loc)
    return config.meta(port,'cost') is None

  @property
  def no_models(self):
    return self._no_model

  def cost(self,block_name,loc,port,handle=None):
    if self._ideal:
      return 0.0

    return get_variance(self._db,self._circ, \
                        block_name,loc,port,handle)


  def input_port(self,block_name,loc,port):
    circ = self._circ
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    total_cost = self.cost(block_name,loc,port)
    if block_name == "integrator" and \
       port == "in":
      config.set_meta(port,'cost',total_cost)
      ForwardVisitor.input_port(self,block_name,loc,port)
      return
    else:
      ForwardVisitor.input_port(self,block_name,loc,port)

    outputs = []
    for output in block.outputs:
      if not config.has_expr(output):
        expr = block.get_dynamics(config.comp_mode,output)
      else:
        expr = config.expr(output,inject=False)

      if port in expr.vars():
        outputs.append(output)

    incomplete,bound = self.classify(block_name,loc,outputs)
    costs = []
    for bound_var in bound:
      costs.append(config.meta(bound_var,'cost'))

    if len(incomplete) > 0:
      print("%s[%s].%s" % (block_name,loc,port))
      print(incomplete)
      raise Exception("incomplete outputs")

    ds_costs = max(costs) if len(costs) > 0 else 0.0
    if self._prop_cost:
      total_cost += ds_costs*0.2
    config.set_meta(port,'cost',total_cost)

  def output_port(self,block_name,loc,port):
    ForwardVisitor.output_port(self,block_name,loc,port)
    circ = self._circ
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    costs,incomplete = [],[]
    for dblk,dloc,dport in \
        circ.get_conns_by_src(block_name,loc,port):
      if not self.is_free(dblk,dloc,dport):
        dconfig = circ.config(dblk,dloc)
        costs.append(dconfig.meta(dport,'cost'))
      else:
        incomplete.append((dblk,dloc,dport))

    if len(incomplete) > 0:
      print("%s[%s].%s" % (block_name,loc,port))
      print(incomplete)
      raise Exception("incomplete destinations")

    total_cost = self.cost(block_name,loc,port)
    ds_costs = max(costs) if len(costs) > 0 else 0.0
    if self._prop_cost:
      total_cost += ds_costs*0.2
    config.set_meta(port,'cost',total_cost)
    for handle in block.handles(config.comp_mode,port):
      c = self.cost(block_name,loc,port,handle)
      config.set_meta(port,'cost',c,handle=handle)

def compute_costs(conc_circ,propagate_cost=False,ideal=False):
  visitor = PropCostVisitor(conc_circ,propagate_cost,ideal=ideal)
  visitor.all(inputs=True)
  return visitor.no_models
