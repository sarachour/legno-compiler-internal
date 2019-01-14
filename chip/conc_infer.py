import chip.props as props
import ops.op as ops
from ops.interval import Interval, IRange, IValue

class IntervalEnv:

  def __init__(self):
    self._visited = {}

  def visited(self,block_name,loc,port,handle=None):
      if not (block_name,loc,port,handle) in self._visited:
          return False
      else:
          return self._visited[(block_name,loc,port,handle)]

  def visit(self,block_name,loc,port,handle=None):
      self._visited[(block_name,loc,port,handle)] = True


def clear_bandwidths_and_intervals(circ):
    for block_name,loc,config in circ.instances():
      config.clear_bandwidths()
      config.clear_intervals()

def math_label_ranges(prog,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.outputs + block.inputs:
            if config.has_label(port):
                label = config.label(port)
                if port in block.outputs:
                    handle = block.get_dynamics(config.comp_mode,\
                                                port).toplevel()
                else:
                    handle = None

                mrng = prog.interval(label)
                mbw = prog.bandwidth(label)
                scf = config.scf(port) if config.has_scf(port) else 1.0
                tau = circ.tau if not circ.tau is None else 1.0
                print("lbl: %s[%s].%s := %s*%s / tau=%s" % \
                      (block_name,loc,port,mrng,scf,tau))
                config.set_interval(port,mrng.scale(scf),\
                                    handle=handle)
                config.set_bandwidth(port,mbw.timescale(tau),\
                                    handle=handle)


def ival_hardware_classify_ports(circ,variables):
    bound,free = [],[]
    for var in variables:
        block_name,loc,port = var
        config = circ.config(block_name,loc)
        if not config.op_range(port) is None:
            bound.append(var)
        else:
            free.append(var)

    return free,bound


def bw_math_classify_ports(circ,variables):
    bound,free = [],[]
    for var in variables:
        block_name,loc,port = var
        config = circ.config(block_name,loc)
        if not config.bandwidth(port) is None:
          bound.append(var)
        else:
          free.append(var)

    return free,bound


def ival_math_classify_ports(circ,variables):
    bound,free = [],[]
    for var in variables:
        block_name,loc,port = var
        config = circ.config(block_name,loc)
        if not config.interval(port) is None:
          bound.append(var)
        else:
          free.append(var)

    return free,bound

def bw_test_visited(env,block,config,loc,port):
  expr = block.get_dynamics(config.comp_mode,port, \
                             scale_mode=config.scale_mode)
  handles = expr.handles()
  # test to see if we have computed the interval
  visited = True
  if not env.visited(block.name,loc,port):
    visited = False
  for handle in handles:
    if not env.visited(block.name,loc,port,handle=handle):
      visited = False

  return visited


def ival_test_visited(env,block,config,loc,port):
  expr = block.get_dynamics(config.comp_mode,port, \
                             scale_mode=config.scale_mode)
  handles = expr.handles()
  # test to see if we have computed the interval
  visited = True
  if not env.visited(block.name,loc,port):
    visited = False
  for handle in handles:
    if not env.visited(block.name,loc,port,handle=handle):
      visited = False

  return visited

def bw_derive_output_port(env,circ,block,config,loc,port):
    expr = block.get_dynamics(config.comp_mode,port, \
                             scale_mode=config.scale_mode)

    if bw_test_visited(env,block,config,loc,port):
        print("[visit] skipping %s[%s].%s" \
              % (block.name,loc,port))
        return True

    # find intervals for free variables
    variables = list(map(lambda v: (block.name,loc,v), expr.vars()))
    free,bound = bw_math_classify_ports(circ, variables)
    for free_block_name,free_loc,free_port in free:
      free_block = circ.board.block(free_block_name)
      bw_derive_port(env,circ,free_block,\
                       circ.config(free_block.name,free_loc),\
                       free_loc,free_port)

    env.visit(block.name,loc,port)
    # compute intervals
    ival_map = config.intervals()
    bw_map = config.bandwidths()
    bandwidths = expr.infer_bandwidth(ival_map,bw_map)

    if config.bandwidth(port) is None:
      print("bw %s[%s].%s = %s" % (block.name,loc,port,bandwidths.bandwidth))
      config.set_bandwidth(port,bandwidths.bandwidth)

    for handle,bandwidth in bandwidths.bindings():
      if not config.bandwidth(port,handle=handle):
        config.set_bandwidth(port,bandwidth,handle=handle)



def ival_derive_output_port(env,circ,block,config,loc,port):
    expr = block.get_dynamics(config.comp_mode,port, \
                             scale_mode=config.scale_mode)

    if ival_test_visited(env,block,config,loc,port):
        print("[visit] skipping %s[%s].%s" \
              % (block.name,loc,port))
        return True

    env.visit(block.name,loc,port)
    # find intervals for free variables
    variables = list(map(lambda v: (block.name,loc,v), expr.vars()))
    free,bound = ival_hardware_classify_ports(circ, variables)
    assert(len(free) == 0)
    free,bound = ival_math_classify_ports(circ, variables)
    for free_block_name,free_loc,free_port in free:
      free_block = circ.board.block(free_block_name)
      ival_derive_port(env,circ,free_block,\
                       circ.config(free_block.name,free_loc),\
                       free_loc,free_port)

    # compute intervals
    ival_map = config.intervals()
    intervals = expr.compute_interval(ival_map)

    if config.interval(port) is None:
        config.set_interval(port,intervals.interval)

    for handle,interval in intervals.bindings():
        if not config.interval(port,handle=handle):
            config.set_interval(port, \
                                interval,handle=handle)





def bw_derive_input_port(env,circ,block,config,loc,port):
    sources = list(circ.get_conns_by_dest(block.name,loc,port))
    free,bound = bw_math_classify_ports(circ,sources)
    for free_block_name,free_loc,free_port in free:
        free_block = circ.board.block(free_block_name)
        bw_derive_port(env,circ,free_block,
                            circ.config(free_block.name,free_loc),\
                            free_loc,free_port)

    scf = config.scf(port) if config.has_scf(port) else 1.0
    dest_expr = ops.Const(0 if not config.has_dac(port) else \
                          config.dac(port)*scf)

    dest_bw = dest_expr.compute_bandwidth({}).bandwidth

    for src_block_name,src_loc,src_port in free+bound:
      config = circ.config(src_block_name,src_loc)
      src_bw = config.bandwidth(src_port)
      if(src_bw is None):
        print("free: <%s>\n" % free)
        print("bound: <%s>\n" % bound)

        raise Exception("unknown bandwidth: %s[%s].%s" % \
                        (src_block_name,src_loc,src_port))

      dest_bw = dest_bw.add(src_bw)

    config = circ.config(block.name,loc)
    config.set_bandwidth(port,dest_bw)
    print("bw in %s[%s].%s => %s" % (block.name,loc,port,dest_bw))



def ival_derive_input_port(env,circ,block,config,loc,port):
    sources = list(circ.get_conns_by_dest(block.name,loc,port))
    free,bound = ival_math_classify_ports(circ,sources)
    for free_block_name,free_loc,free_port in free:
        free_block = circ.board.block(free_block_name)
        ival_derive_port(env,circ,free_block,
                            circ.config(free_block.name,free_loc),\
                            free_loc,free_port)

    scf = config.scf(port) if config.has_scf(port) else 1.0
    dest_expr = ops.Const(0 if not config.has_dac(port) \
                          else scf*config.dac(port))
    dest_ival = dest_expr.compute_interval({}).interval

    for src_block_name,src_loc,src_port in free+bound:
      config = circ.config(src_block_name,src_loc)
      src_ival = config.interval(src_port)
      if(src_ival is None):
        print("free: <%s>\n" % free)
        print("bound: <%s>\n" % bound)

        raise Exception("unknown interval: %s[%s].%s" % \
                        (src_block_name,src_loc,src_port))

      dest_ival = dest_ival.add(src_ival)


    config = circ.config(block.name,loc)
    config.set_interval(port,dest_ival)
    print("ival in %s[%s].%s => %s" % (block.name,loc,port,dest_ival))



def bw_derive_port(env,circ,block,config,loc,port):
    if block.is_input(port):
        bw_derive_input_port(env,circ,block,config,loc,port)

    elif block.is_output(port):
        bw_derive_output_port(env,circ,block,config,loc,port)

    else:
        raise Exception("what the fuck...")



def ival_derive_port(env,circ,block,config,loc,port):
    if block.is_input(port):
        ival_derive_input_port(env,circ,block,config,loc,port)

    elif block.is_output(port):
        ival_derive_output_port(env,circ,block,config,loc,port)

    else:
        raise Exception("what the fuck...")


def ival_port_to_range(block,config,port,handle=None):
  assert(not config.scale_mode is None)
  assert(not config.comp_mode is None)
  return block.props(config.comp_mode,\
                       config.scale_mode,\
                       port,\
                       handle=handle).interval()

def hw_port_op_ranges(circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        mode = config.comp_mode
        for port in block.inputs + block.outputs:
            hwrng = ival_port_to_range(block,config,port)
            config.set_op_range(port,hwrng)
            for handle in block.handles(mode,port):
                hwrng = ival_port_to_range(block,config,port, \
                                           handle=handle)
                config.set_op_range(port,hwrng,\
                                    handle=handle)
def bind_intervals(env,prog,circ):
    # bind operating ranges for ports
  for block_name,loc,config in circ.instances():
    block = circ.board.block(block_name)
    for out_port in block.outputs:
      ival_derive_port(env,circ,block,config,loc,out_port)

  for block_name,loc,config in circ.instances():
    block = circ.board.block(block_name)
    for port in block.outputs + block.inputs:
      assert(not config.op_range(port) is None)

def bind_bandwidths(env,prog,circ):
    # bind operating ranges for ports
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out_port in block.outputs:
            bw_derive_port(env,circ,block,config,loc,out_port)



def infer(prog,circ):
  hw_port_op_ranges(circ)
  # clear any already computed bandwidths and intervals
  clear_bandwidths_and_intervals(circ)
  # math label ranges
  math_label_ranges(prog,circ)
  print("==== intervals ====")
  env= IntervalEnv()
  bind_intervals(env,prog,circ)
  print("==== bandwidths ====")
  env= IntervalEnv()
  bind_bandwidths(env,prog,circ)
