import ops.op as op
import numpy as np

class NoiseEnv:

  def __init__(self):
    self._bindings = {}

  def bind(self,var,noise):
    self._bindings[var] = noise

def nz_expr(expr,config,bindings):
  if expr.op == op.Op.VAR:
    if config.has_dac(expr.name):
      coeff = abs(config.dac(expr.name))
    else:
      coeff = 1.0

    return coeff*bindings[expr.name]

  if expr.op == op.Op.MULT:
    nz1 = nz_expr(expr.arg1,config,bindings)
    nz2 = nz_expr(expr.arg2,config,bindings)
    return nz1*nz2

  elif expr.op == op.Op.INTEG:
    nz1 = nz_expr(expr.deriv,config,bindings)
    nz2 = nz_expr(expr.init_cond,config,bindings)
    print(nz1,nz2)
    return nz1

  else:
    raise Exception("unhandled: <%s>" % expr)

def noise_analysis(nzenv,board,circ,block_name,loc,port,visited=[]):
  block = board.block(block_name)
  config = circ.config(block_name,loc)
  if (block_name,loc,port) in visited:
    print("terminal %s[%s].%s" % (block_name,loc,port))
    return 0.0

  new_visited = visited+[(block_name,loc,port)]

  print("recurse %s[%s].%s" % (block_name,loc,port))
  if block.is_output(port):
    expr = block.get_dynamics(config.comp_mode,port)
    bindings = {}
    for input_var in expr.vars():
      noise = noise_analysis(nzenv,board,circ,block_name,loc,input_var,
                             visited=new_visited)
      bindings[input_var] = noise

    print("expr: %s" % expr)
    print(config)
    scale_mode = tuple(config.scale_mode) if not config.scale_mode is None \
                 else "*"

    scf = block.scale_factor(config.comp_mode,\
                             scale_mode,port)
    print("scf: %s" % scf)
    out_noise = nz_expr(expr,config,bindings)*scf
    out_noise += 1.0
    return out_noise

  elif block.is_input(port):
    bindings = []
    for (sblk,sloc,sport) in \
        circ.get_conns_by_dest(block_name,loc,port):
      noise = noise_analysis(nzenv,board,circ,sblk,sloc,sport,
                             visited=new_visited)
      bindings.append(noise)

    if len(bindings) == 0:
      return 1.0

    return sum(bindings)


def compute_score(board,circ,block_name,loc,port,noise):
  block = board.block(block_name)
  config = circ.config(block_name,loc)
  scf = config.scf(port)
  label = config.label(port)

  mmin,mmax = circ.interval(label)
  signal_mag = scf*max(abs(mmin),abs(mmax))
  return np.log10(signal_mag/noise)

def execute(board,circ):
  endpoints = []
  for handle,block,loc in board.handles():
    if circ.in_use(block,loc):
      for port,label,scf,kind in \
          circ.config(block,loc).labels():
        endpoints.append((block,loc,port,label))

  score = 0
  for block_name,loc,port,label in endpoints:
    print("%s[%s].%s := %s" % (block,loc,port,label))
    noise = noise_analysis(NoiseEnv(),board,circ, \
                           block_name,loc,port,visited=[])
    this_score = compute_score(board,circ,block_name,loc,port,noise)
    score += this_score

  return score
