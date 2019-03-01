import itertools
import ops.nop as nop
import util.util as util
import math

def get_iface_ports(circuit):
  for block_name,loc,config in circuit.instances():
    if not circuit.board.handle_by_inst(block_name,loc) \
       is None:
      block = circuit.board.block(block_name)
      for out in block.outputs:
        ports.append((block_name,loc,out))
  return

def get_integrator_ports(circuit):
  ports = []
  for block_name,loc,config in circuit.instances():
    block = circuit.board.block(block_name)
    if block_name != "integrator":
      continue
    for out in block.outputs:
      ports.append((block_name,loc,out))

  return ports

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

def gpkit_ref_expr(jenv,varmap,circ,expr,last_index=False):
  variables = expr.vars()
  result = 1.0
  for var in variables:
    # values
    if expr.op == nop.NOpType.SIG:
      (block,loc),port = expr.instance,expr.port
      scival = circ.config(block,loc).interval(port)
      scvarname = jenv.get_scvar(block,loc,port)
      expo = expr.power
      print(rng,varmap[scvarname]*scival.bound)
      input()
      result *= (rng*varmap[scvarname])**expo

    elif expr.op == nop.NOpType.FREQ:
      expo = expr.power
      if last_index:
        result *= varmap['tau']**expo

      elif expr.op == nop.NOpType.REF:
        continue

  return result


def gpkit_expr(jenv,varmap,circ,expr,refs,nstdevs=3):
  def recurse(e):
    return gpkit_expr(jenv,varmap,circ,e,refs,nstdevs)

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
      #value = fmax*varmap['tau']**expo
      value = 1.0
      return value

    elif expr.op == nop.NOpType.REF:
      block,loc = expr.instance
      port = expr.port
      return refs[(block,loc,port)]

  # values
  elif expr.op == nop.NOpType.CONST_RV:
    return gpkit_value(expr.sigma*nstdevs+expr.mu)

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

def compute_reference(varmap,jenv,circ, \
                      block_name,loc,port,model,refs,method):
  gpkit_mean = gpkit_ref_expr(jenv,varmap,circ,model.mean)
  gpkit_variance = gpkit_ref_expr(jenv,varmap,circ,model.variance)
  # compute signal
  scvarname = jenv.get_scvar(block_name,loc,port)
  scival = circ.config(block_name,loc).interval(port)
  signal = varmap[scvarname]*scival.bound

  if method == 'low_snr':
    return gpkit_mean*signal**(-1) + \
      gpkit_variance*signal**(-1)

  elif method == 'low':
    return gpkit_mean + gpkit_variance

  else:
    raise Exception(method)



def compute_objective(varmap,jenv,circ, \
                      block_name,loc,port,model,refs,method):
  gpkit_mean = gpkit_expr(jenv,varmap,circ,model.mean,
                          refs)
  gpkit_variance = gpkit_expr(jenv,varmap,circ,model.variance,
                              refs)
  # compute signal
  scvarname = jenv.get_scvar(block_name,loc,port)
  scival = circ.config(block_name,loc).interval(port)
  signal = varmap[scvarname]*scival.bound

  if method == 'low_snr':
    return gpkit_mean*signal**(-1) + \
      gpkit_variance*signal**(-1)

  elif method == 'low':
    return gpkit_mean + gpkit_variance

  else:
    raise Exception(method)

def compute(varmap,jenv,circ,models,ports,method='low-snr'):
  time_constant = 1.0/circ.board.time_constant
  Jtau = varmap['tau']
  refs = {}
  for model,(block_name,loc,port) \
      in zip(models,ports):
    ref = compute_reference(varmap,jenv,circ, \
                            block_name,loc,port,model,refs,method)
    refs[(block_name,loc,port)] = ref

  for model,(block_name,loc,port) in zip(models,ports):
    gpkit_obj = compute_objective(varmap,jenv,circ, \
                            block_name,loc,port,model,refs,method)


  return [],gpkit_obj

def low_noise(circuit,jenv,varmap):
  ports = get_integrator_ports(circuit)
  models = []
  for block_name,loc,out in ports:
    model = circuit.config(block_name,loc) \
           .propagated_noise(out)
    models.append(model)

  cstr,obj = compute(varmap,jenv,circuit,models,ports, \
                          method='low_snr')
  yield cstr,obj
