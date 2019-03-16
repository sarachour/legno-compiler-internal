import itertools
import ops.nop as nop
import util.util as util
import compiler.common.evaluator_heuristic as evalheur
import compiler.jaunt_pass.objective.obj as optlib
import compiler.jaunt_pass.objective.basic_obj as boptlib
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
      if jenv.has_inject_var(block,loc,port):
        injvarname = jenv.get_inject_var(block,loc,port)
        scexpr = varmap[scvarname]*varmap[injvarname]
      else:
        scexpr = varmap[scvarname]

      scival = config.interval(port)
      result = (scexpr*scival.bound)**expo
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
  scival = circ.config(block_name,loc).interval(port)
  scvarname = jenv.get_scvar(block_name,loc,port)
  if jenv.has_inject_var(block_name,loc,port):
    injvarname = jenv.get_inject_var(block,loc,port)
    scexpr = varmap[scvarname]*varmap[injvarname]
  else:
    scexpr = varmap[scvarname]

  if scival.bound > 0:
    signal = scexpr*scival.bound
  else:
    signal = None

  return gpkit_mean,gpkit_variance,signal

def compute_distributions(varmap,jenv,circ,models,ports):
  means = {}
  variances = {}
  signals = {}
  for model,(block_name,loc,port) \
      in zip(models,ports):
    if model == None:
      continue
    mean,variance,sig = compute_expression(varmap,jenv,circ, \
                                  block_name,loc,port,model,
                                  refs=None)
    signals[(block_name,loc,port)] = sig
    means[(block_name,loc,port)] =mean
    variances[(block_name,loc,port)] =variance
  return signals,means,variances

def compute_snr_info(ports,signals,means,variances):
  signal = 1.0
  noise = 1.0
  snr = 0.0
  for block_name,loc,port in ports:
    if not (block_name,loc,port) in signals:
      continue

    sig = signals[(block_name,loc,port)]
    nz = variances[(block_name,loc,port)]
    if not sig is None:
      signal *= (sig**-1)
      noise *= nz
      snr += (sig**-1)*(nz)

  return signal,noise,snr

def compute(varmap,jenv,circ,models,ports,method='low-snr'):
  time_constant = 1.0/circ.board.time_constant
  Jtau = varmap['tau']
  signals,means,variances = compute_distributions(varmap,jenv,circ,models,ports)
  if method == 'low_snr':
    sig,nz,snr = compute_snr_info(ports,signals,means,variances)
    #return nz*(sig**-1)
    return snr

  elif method == 'snr_to_tau':
    sig,nz,snr = compute_snr_info(ports,signals,means,variances)
    return snr*(Jtau**(-1))

  else:
    raise Exception("unknown method <%s>" % method)

class FastLowNoiseObjFunc(optlib.JauntObjectiveFunction):

  def __init__(self,obj):
    optlib.JauntObjectiveFunction.__init__(self,obj)

  @staticmethod
  def name():
    return 'lo-noise-fast'

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
                  method='snr_to_tau')
    yield FastLowNoiseObjFunc(opt)

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



class MaxSNRAtSpeedObjFunc(boptlib.MultSpeedObjFunc):

  def __init__(self,obj,idx,tau,cstrs):
    boptlib.MultSpeedObjFunc.__init__(self,obj,idx,tau,cstrs)

  def mktag(self,idx):
    return "lnz-tau%d" % idx


  @staticmethod
  def name():
    return "nz-sweep-tau"


  @staticmethod
  def mkobj(circ,jobj,varmap,idx,tau,cstrs):
    obj = list(LowNoiseObjFunc.make(circ,jobj,varmap))[0].objective()
    return MaxSNRAtSpeedObjFunc(obj,
                                idx=idx,
                                tau=tau,
                                cstrs=cstrs)

  @staticmethod
  def make(circ,jobj,varmap,n=7):
    return boptlib.MultSpeedObjFunc.make(MaxSNRAtSpeedObjFunc,circ, \
                                 jobj,varmap,n=n)
