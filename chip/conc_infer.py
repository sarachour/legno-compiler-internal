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

def ival_math_dac_ranges(env,circ):
     for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.inputs + block.outputs:
            if config.has_dac(port):
                value = config.dac(port)
                mrng = IValue(value)
                print("val: %s[%s].%s := %s" % (block_name, \
                                                loc,\
                                                port, \
                                                mrng))
                config.set_interval(port,mrng)

def ival_math_label_ranges(env,circ):
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
                lb,ub = circ.interval(label)
                mrng = IRange(lb,ub)
                print("lbl: %s[%s].%s := %s" % \
                      (block_name,loc,port,mrng))
                config.set_interval(port,mrng,\
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


def ival_math_classify_ports(circ,variables):
    bound,free = [],[]
    for var in variables:
        block_name,loc,port = var
        config = circ.config(block_name,loc)
        if not config.interval(port) is None:
          print("bnd %s[%s].%s = %s" % (block_name,loc,port,config.interval(port)))
          bound.append(var)
        else:
          free.append(var)

    return free,bound

def ival_derive_output_port(env,circ,block,config,loc,port):
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

    if visited:
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
    varmap = config.intervals()
    intervals = expr.interval(varmap)

    if config.interval(port) is None:
        config.set_interval(port,intervals.interval)

    for handle,interval in intervals.bindings():
        if not config.interval(port,handle=handle):
            config.set_interval(port, \
                                interval,handle=handle)





def ival_derive_input_port(env,circ,block,config,loc,port):
    sources = list(circ.get_conns_by_dest(block.name,loc,port))
    free,bound = ival_math_classify_ports(circ,sources)
    assert(len(sources) > 0)
    for free_block_name,free_loc,free_port in free:
        free_block = circ.board.block(free_block_name)
        ival_derive_port(env,circ,free_block,
                            circ.config(free_block.name,free_loc),\
                            free_loc,free_port)

    expr_ival = None
    if config.has_dac(port):
      expr_ival = IValue(config.dac(port))

    for src_block_name,src_loc,src_port in free+bound:
      config = circ.config(src_block_name,src_loc)
      src_ival = config.interval(src_port)
      expr_ival = src_ival if expr_ival is None else \
                  expr_ival.add(src_ival)

    config = circ.config(block.name,loc)
    config.set_interval(port,expr_ival)
    print("ival in %s[%s].%s => %s" % (block.name,loc,port,expr_ival))



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

def ival_hw_port_op_ranges(env,circ):
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
def bind_intervals(env,circ):
    # bind operating ranges for ports
    ival_hw_port_op_ranges(env,circ)
    ival_math_dac_ranges(env,circ)
    ival_math_label_ranges(env,circ)
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out_port in block.outputs:
            ival_derive_port(env,circ,block,config,loc,out_port)

    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.outputs + block.inputs:
            assert(not config.op_range(port) is None)

def infer(circ):
  env= IntervalEnv()
  bind_intervals(env,circ)
