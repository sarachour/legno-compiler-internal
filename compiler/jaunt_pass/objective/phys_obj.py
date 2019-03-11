import itertools
import ops.nop as nop
import util.util as util
import compiler.common.evaluator_heuristic as evalheur
import compiler.jaunt_pass.objective.obj as optlib
import math

def gpkit_mult(expr):
  freqs = list(filter(lambda arg: arg.op == nop.NOpType.FREQ, \
                 expr.args()))
  args = list(filter(lambda arg: arg.op != nop.NOpType.FREQ, \
                 expr.args()))
  print(freqs)
  print(args)
  raise NotImplementedError

def gpkit_value(val):

  if val > 0:
    return val
  # any terms with negative values is approximated as a flat line
  else:
    return -val

def gpkit_expr(jenv,varmap,circ,expr,refs):
  def recurse(e):
    return gpkit_expr(jenv,varmap,circ,e,refs=refs)

  if isinstance(expr,nop.NVar):
    # variables
    block,loc = expr.instance
    port = expr.port
    expo = expr.power
    config = circ.config(block,loc)
    if expr.op == nop.NOpType.SIG:
      scvarname = jenv.get_scvar(block,loc,port)
      scival = config.interval(port)
      result = (varmap[scvarname]*scival.bound)**expo
      return result

    elif expr.op == nop.NOpType.FREQ:
      # compute integral
      fmax = circ.config(block,loc).bandwidth(port).bandwidth
      tc = circ.board.time_constant
      value = (tc*fmax*varmap['tau'])**expo
      return value

    elif expr.op == nop.NOpType.REF:
      block,loc = expr.instance
      port = expr.port
      if refs is None:
        raise Exception("cannot have reference in reference.")
      return refs[(block,loc,port)]

  # values
  elif expr.op == nop.NOpType.CONST_RV:
    # the mean and variance have been made deterministic/separated
    assert(expr.sigma == 0.0)
    return gpkit_value(abs(expr.mu))

  # expressions
  elif expr.op == nop.NOpType.MULT:
    if not (expr.is_posynomial()):
      raise Exception("not posynomial: %s" % expr)
    result = 1.0
    for arg in expr.args():
      result *= recurse(arg)
    return result

  elif expr.op == nop.NOpType.ADD:
    result = 0
    for arg in expr.args():
      result += recurse(arg)
    return result

  else:
    raise Exception(expr)

def compute_expression(varmap,jenv,circ, \
                       block_name,loc,port,model,refs):
  gpkit_mean = gpkit_expr(jenv,varmap,circ, \
                          model.mean,refs)
  gpkit_variance = gpkit_expr(jenv,varmap,circ, \
                              model.variance,refs)


  # compute signal
  scvarname = jenv.get_scvar(block_name,loc,port)
  scival = circ.config(block_name,loc).interval(port)
  signal = varmap[scvarname]*scival.bound
  return gpkit_mean,gpkit_variance,signal




def compute(varmap,jenv,circ,models,ports,method='low-snr'):
  time_constant = 1.0/circ.board.time_constant
  Jtau = varmap['tau']
  means = {}
  variances = {}
  signals = {}
  for model,(block_name,loc,port) \
      in zip(models,ports):
    mean,variance,sig = compute_expression(varmap,jenv,circ, \
                                  block_name,loc,port,model,
                                  refs=None)
    signals[(block_name,loc,port)] = sig
    means[(block_name,loc,port)] =mean
    variances[(block_name,loc,port)] =variance

  if method == 'low_snr':
    signal = 1.0
    noise = 1.0
    snr = 0.0
    for block_name,loc,port in ports:
      sig = signals[(block_name,loc,port)]
      nz = variances[(block_name,loc,port)]
      print(block_name,loc,port)
      print(sig)
      signal *= (sig**-1)
      noise *= nz
      snr += (sig**-1)*(nz)

    opt = signal+signal*noise
    return opt
  else:
    raise Exception("unknown method <%s>" % method)

class LowNoiseObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return 'lo-noise'

  @staticmethod
  def make(circuit,jobj,varmap):
    jenv = jobj.jenv
    ports = evalheur.get_ports(circuit)
    models = []
    for block_name,loc,out in ports:
      model = circuit.config(block_name,loc) \
                     .propagated_noise(out)
      models.append(model)

    opt = compute(varmap,jenv,circuit,models,ports, \
                  method='low_snr')
    yield LowNoiseObjFunc(opt)
