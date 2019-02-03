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

def gpkit_expr(jenv,varmap,circ,ival,expr,last_index=False):
  def recurse(e):
    return gpkit_expr(jenv,varmap,circ,ival,e,last_index=False)

  if expr.op == nop.NOpType.ZERO:
    return 0

  # variables
  elif expr.op == nop.NOpType.SIG:
    block,loc = expr.instance
    port = expr.port
    scvarname = jenv.get_scvar(block,loc,port)
    scival = circ.config(block,loc).interval(port)
    expo = expr.power
    result = (varmap[scvarname]*scival.bound)**expo
    return result

  elif expr.op == nop.NOpType.FREQ:
    expo = expr.power
    value = (ival.spread*circ.board.time_constant)**(expo+1)
    value *= 1.0/(expo+1)
    if last_index:
      value *= varmap['tau']
    return value

  # values
  elif expr.op == nop.NOpType.CONST_VAL:
    return gpkit_value(expr.mu)

  elif expr.op == nop.NOpType.CONST_RV:
    return gpkit_value(expr.sigma)

  # expressions
  elif expr.op == nop.NOpType.MULT:
    result = 1.0
    expo = 1 if expr.is_posynomial() else -1
    for arg in expr.args():
      result *= recurse(arg)**expo
    return result

  elif expr.op == nop.NOpType.ADD:
    result = 0
    for arg in expr.args():
      result += recurse(arg)
    return result

  else:
    raise Exception(expr)

def compute_objective(varmap,jenv,circ, \
                      block_name,loc,port,model,idx,method,
                      last_index=False):
  ival,mean,variance = model.function(idx)
  gpkit_mean = gpkit_expr(jenv,varmap,circ,ival,mean,last_index)
  gpkit_variance = gpkit_expr(jenv,varmap,circ,ival,variance,last_index)
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
  options = list(map(lambda m: range(0,m.size()), models))
  time_constant = 1.0/circ.board.time_constant
  Jtau = varmap['tau']
  #for indices in itertools.product(*options):
  for indices in zip(*options):
    cstrs = []
    objs = []
    for idx,model,(block_name,loc,port) \
        in zip(indices,models,ports):
      config = circ.config(block_name,loc)
      fmax = config.bandwidth(port).fmax

      ival = model.interval(idx)
      term = Jtau*fmax*time_constant
      if not util.pos_inf(ival.upper):
        cstrs.append(term <= ival.upper)
      if ival.lower > 0:
        cstrs.append(term >= ival.lower)

      total_obj = 0
      for k in range(0,idx+1):
        obj = compute_objective(varmap,jenv,circ, \
                          block_name,loc,port,model,idx,method)
        total_obj += obj

      if total_obj != 0:
        objs.append(total_obj)


    # minimizes function
    final_obj = 0
    for obj in objs:
      final_obj += obj

    # noise to signal ratio (NSR)
    yield cstrs,final_obj


def low_noise(circuit,jenv,varmap):
  ports = get_integrator_ports(circuit)
  models = []
  for block_name,loc,out in ports:
    model = circuit.config(block_name,loc) \
           .propagated_noise(out)
    models.append(model)

  for cstr,obj in compute(varmap,jenv,circuit,models,ports, \
                          method='low_snr'):
    yield cstr,obj

def low_bias(circuit,jenv,varmap):
  ports = get_integrator_ports(circuit)
  models = []
  for block_name,loc,out in ports:
    model = circuit.config(block_name,loc) \
           .propagated_bias(out)
    models.append(model)

  for cstr,obj in compute(varmap,jenv,circuit,models,ports, \
                          method='low_snr'):
    yield cstr,obj

def low_delay(circuit,jenv,varmap):
  ports = get_integrator_ports(circuit)
  models = []
  for block_name,loc,out in ports:
    model = circuit.config(block_name,loc) \
           .propagated_bias(out)
    models.append(model)

  for cstr,obj in compute(varmap,jenv,circuit,models,ports, \
                          method='low'):
    yield cstr,obj
