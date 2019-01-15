import ops.op as op
import numpy as np
import ops.interval as interval
from compiler.skelt_pass.common import NoiseEnv

def cpn_classify_ports(config,variables):
  free,bound = [],[]
  for variable in variables:
    if config.propagated_noise(variable) is None:
      free.append(variable)
    else:
      bound.append(variable)
  return free,bound

def cpn_visit_input_port(nzenv,circ,block,loc,config,port):
  noise = interval.Interval.type_infer(0,0)
  for sblk,sloc,sport in \
      circ.get_conns_by_dest(block.name,loc,port):
    src_config = circ.config(sblk,sloc)
    if src_config.propagated_noise(sport) is None:
      cpn_visit_port(nzenv,circ,sblk,sloc,src_config,sport)

    src_nz = src_config.propagated_noise(sport)
    if not src_nz is None:
      noise = noise.add(src_nz)
    else:
      print("[warn] %s[%s].%s has no prop-noise" % (sblk,sloc,sport))

  print("nz out %s[%s].%s = %s" % (block.name,loc,port,noise))
  config.set_propagated_noise(port,noise)


def cpn_visit_output_port(nzenv,circ,block,loc,config,port):
  expr = config.dynamics(block,port)
  free,bound = cpn_classify_ports(config,expr.vars())
  if nzenv.visited(block.name,loc,port):
    return

  nzenv.visit(block.name,loc,port)
  for free_var in free:
    cpn_visit_port(nzenv,circ,block.name,loc,config,free_var)

  pnz_dict = config.all_propagated_noise()
  # if integral, strip integral sign.
  if expr.op == op.OpType.INTEG:
    prop_noise = expr.deriv.compute_interval(pnz_dict)
  else:
    prop_noise = expr.compute_interval(pnz_dict)

  gen_noise = config.generated_noise(port)
  total_noise = prop_noise.interval.add(gen_noise)
  print("nz out %s[%s].%s = %s" % (block.name,loc,port,total_noise))
  config.set_propagated_noise(port,total_noise)



def cpn_visit_port(nzenv,circ,block_name,loc,config,port):
  block = circ.board.block(block_name)
  if block.is_input(port):
    cpn_visit_input_port(nzenv,circ,block,loc,config,port)
  elif block.is_output(port):
    cpn_visit_output_port(nzenv,circ,block,loc,config,port)

def compute(circ):
  nzenv = NoiseEnv()
  for handle,block_name,loc in circ.board.handles():
      if circ.in_use(block_name,loc):
        config = circ.config(block_name,loc)
        for port,label,kind in config.labels():
          cpn_visit_port(nzenv,circ,block_name,loc,config,port)

