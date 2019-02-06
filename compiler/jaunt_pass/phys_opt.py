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
      block,loc = expr.instance
      port = expr.port
      scvarname = jenv.get_scvar(block,loc,port)
      expo = expr.power
      result *= (varmap[scvarname])**expo

    elif expr.op == nop.NOpType.FREQ:
      expo = expr.power
      if last_index:
        result *= varmap['tau']**expo

      elif expr.op == nop.NOpType.REF:
        continue

  return result


def gpkit_expr(jenv,varmap,circ,expr,refs,cstrs,nstdevs=3):
  def recurse(e):
    return gpkit_expr(jenv,varmap,circ,e,refs,cstrs,nstdevs)

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
      frng = cstrs[(block,loc,port)]
      fweight = (fmax-frng.lower)/frng.spread
      fweight = 0.0 if fweight <= 0.0 else fweight
      value = fweight*varmap['tau']**expo
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
                      block_name,loc,port,model,refs,idx,method,
                      last_index=False):
  mean,variance = model.model(idx)
  gpkit_mean = gpkit_ref_expr(jenv,varmap,circ,mean, \
                              last_index)
  gpkit_variance = gpkit_ref_expr(jenv,varmap,circ,variance, \
                                  last_index)
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
                      block_name,loc,port,model,refs,idx,method,
                      last_index=False):
  mean,variance = model.model(idx)
  cstrs = model.cstrs.constraints(idx)
  gpkit_mean = gpkit_expr(jenv,varmap,circ,mean,
                          refs,cstrs)
  gpkit_variance = gpkit_expr(jenv,varmap,circ,variance,
                              refs,cstrs)
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
    gpkit_cstrs = []
    objs = []
    refs = {}
    # compute references for propagation
    for idx,model,(block_name,loc,port) \
        in zip(indices,models,ports):
      total_ref = 0
      for k in range(0,idx+1):
        ref = compute_reference(varmap,jenv,circ, \
                                block_name,loc,port,model,refs,idx,method)
        total_ref += ref
      refs[(block_name,loc,port)] = ref

    # compute constraints
    for idx,model,(block_name,loc,port) \
        in zip(indices,models,ports):

      cstrs = model.cstrs.constraints(idx)
      for (cstr_block,cstr_loc,cstr_port),ival in cstrs.items():
        config = circ.config(cstr_block,cstr_loc)
        fmax = config.bandwidth(cstr_port).fmax
        term = Jtau*fmax*time_constant
        if not util.pos_inf(ival.upper):
          gpkit_cstrs.append(term <= ival.upper)
        if ival.lower > 0:
          gpkit_cstrs.append(term >= ival.lower)

      gpkit_obj = 0
      for k in range(0,idx+1):
        obj = compute_objective(varmap,jenv,circ, \
                                block_name,loc,port,model,refs,idx,method)
        gpkit_obj += obj

      if gpkit_obj != 0:
        objs.append(gpkit_obj)


    # minimizes function
    gpkit_obj = 0
    for obj in objs:
      gpkit_obj += obj

    # noise to signal ratio (NSR)
    yield gpkit_cstrs,gpkit_obj


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
