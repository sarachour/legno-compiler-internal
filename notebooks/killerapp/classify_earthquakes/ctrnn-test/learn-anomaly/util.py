from enum import Enum
import math
import neat

def sinc(x):
  return 1.0 if x == 0 else math.sin(x) / x

def identity(x):
  return x

class ActivationFunction(Enum):
  SINC = "sinc"
  IDENTITY = "identity"

  def to_python_func(self):
    if self == ActivationFunction.SINC:
      return sinc
    elif self == ActivationFunction.IDENTITY:
      return identity

  def to_expr(self,arg):
    if self == ActivationFunction.SINC:
      return "sinc(%s)" % arg
    elif self == ActivationFunction.IDENTITY:
      return "%s" % arg

class Relation(Enum):
  FUNC = "func"
  DIFFEQ = "diffeq"

class VarMap:

  def __init__(self):
    self._count = {}
    self._map = {}
    self._types = {}

  def to_json(self):
    return {
      'idents':self._map,
      'types':self._types
    }

  def _get(self,v,n,define=True):
    if n in self._map:
      return self._map[n]

    if not v in self._count:
      self._count[v] = 0

    varname = "%s%d" % (v,self._count[v])
    self._count[v] += 1
    self._map[n] = varname
    return varname

  def get_input(self,ident):
    v = self._get("i",ident)
    self._types[v] = "input"
    return v

  def get_output(self,ident):
    v = self._get("o",ident)
    self._types[v] = "output"
    return v

  def get_hidden(self,ident):
    v = self._get("x",ident)
    self._types[v] = "hidden"
    return v

  def __repr__(self):
    s = "--- varmap ---\n"
    for i,v in self._map.items():
      s += "%d=%s\n" % (i,v)
    return s

def rnn_to_relations(net, \
                   activation_function=ActivationFunction.IDENTITY):
  vmap = VarMap()
  for idx in net.input_nodes:
    vmap.get_input(idx)
  for idx in net.output_nodes:
    vmap.get_output(idx)

  bindings = {}
  for (node_key, act, agg, bias, response, inputs) in net.node_evals:
    terms = []
    for i,w in inputs:
      term = "%f*%s" % (w,vmap.get_hidden(i))
      terms.append(term)
    subexpr = "+".join(terms)
    expr = "%f+%f*(%s)" % (bias,response,subexpr)
    act_expr = activation_function.to_expr(expr)
    var = vmap.get_hidden(node_key)
    bindings[var] = (act_expr,Relation.FUNC.value)

  return vmap,bindings


def ctrnn_to_diffeqs(net, \
                     activation_function=ActivationFunction.IDENTITY):
  vmap = VarMap()
  for idx in net.input_nodes:
    vmap.get_input(idx)
  for idx in net.output_nodes:
    vmap.get_output(idx)

  for node_key, ne in iteritems(net.node_evals):
    terms = []
    for i,w in ne.links:
      term = "%f*%s" % (w,vmap.get_hidden(i))
      terms.append(term)

    subexpr = "+".join(terms)
    expr = "%f+%f*(%s)" % (ne.bias,ne.response,subexpr)
    act_expr = activation_function.to_expr(expr)
    var = vmap.get_hidden(node_key)
    deriv_expr = "{tau}*{act_expr}+{tau}*(-{state_var})".format(
      act_expr=act_expr,
      state_var=var,
      tau=1.0/ne.time_constant
    )
    bindings[var] = (deriv_expr,Relation.DIFFEQ.value)

  return vmap,bindings

def to_system(net,activation_function=ActivationFunction.IDENTITY):
  if isinstance(net, neat.nn.RecurrentNetwork):
    vmap,bindings = rnn_to_relations(net,activation_function)
  elif isinstance(net, neat.ctrnn.CTRNN):
    vmap,bindings = ctrnn_to_diffeqs(net,activation_function)

  return {
    'variable_map':vmap.to_json(),
    'bindings':bindings
  }
