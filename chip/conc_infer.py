import chip.props as props
import ops.op as ops
from ops.interval import Interval, IRange, IValue

class IntervalEnv:

  def __init__(self):
    self._math_ivals = {}
    self._hw_ivals = {}
    self._bandwidths = {}
    self._scfs = {}
    self._coeffs = {}
    self._visited = {}

  def visited(self,block_name,loc,port,handle=None):
      if not (block_name,loc,port,handle) in self._visited:
          return False
      else:
          return self._visited[(block_name,loc,port,handle)]

  def visit(self,block_name,loc,port,handle=None):
      self._visited[(block_name,loc,port,handle)] = True

  def coeff(self,block_name,loc,port,handle=None):
    if not (block_name,loc,port,handle) in self._coeffs:
      return 1.0
    else:
      return self._coeffs[(block_name,loc,port,handle)]

  def set_coeff(self,block_name,loc,port,value,handle=None):
      self._coeffs[(block_name,loc,port,handle)] = value


  def scf(self,block_name,loc,port,handle=None):
    if not (block_name,loc,port,handle) in self._scfs:
      return 1.0
    else:
      return self._scfs[(block_name,loc,port,handle)]

  def set_scf(self,block_name,loc,port,value,handle=None):
      self._scfs[(block_name,loc,port,handle)] = value

  def set_hardware_interval(self,block_name,loc,port,ival,handle=None):
      if not (isinstance(ival,Interval)):
          raise Exception("not ival <%s>.T<%s>" % \
                          (ival,ival.__class__.__name__))

      assert(not (block_name,loc,port,handle) in \
             self._hw_ivals)

      self._hw_ivals[(block_name,loc,port,handle)] = ival

  def set_math_interval(self,block_name,loc,port,interval,handle=None):
      if not (isinstance(interval,Interval)):
          raise Exception("not interval <%s>.T<%s>" % \
                          (interval,interval.__class__.__name__))

      assert(not (block_name,loc,port,handle) in \
             self._math_ivals)
      self._math_ivals[(block_name,loc,port,handle)] = interval


  def has_hardware_interval(self,block_name,loc,port,handle=None):
      return (block_name,loc,port,handle) in self._hw_ivals


  def has_math_interval(self,block_name,loc,port,handle=None):
      return (block_name,loc,port,handle) in self._math_ivals

  def hardware_interval(self,block_name,loc,port,handle=None):
      key = (block_name,loc,port,handle)
      if not key in self._hw_ivals:
          return None
      else:
          return self._hw_ivals[key]

  def math_interval(self,block_name,loc,port,handle=None):
      key = (block_name,loc,port,handle)
      if not key in self._math_ivals:
          return None
      else:
          return self._math_ivals[key]

  def math_intervals(self,block_name,loc,ports,handle=None):
      missing = False
      bindings = []
      for port in ports:
          key = (block_name,loc,port,handle)
          if key in self._math_ivals:
              interval = self._math_ivals[key]
          else:
              interval = None
              missing = True

          bindings.append((port,interval))

      return not missing, bindings


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
                env.set_math_interval(block_name,loc,port,mrng)

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
                env.set_math_interval(block_name,loc,port,mrng,\
                                    handle=handle)

def ival_hardware_classify_ports(env,variables):
    bound,free = [],[]
    for var in variables:
        block_name,loc,port = var
        if env.has_hardware_range(block_name,loc,port):
            bound.append(var)
        else:
            free.append(var)

    return free,bound


def ival_math_classify_ports(env,variables):
    bound,free = [],[]
    for var in variables:
        block_name,loc,port = var
        if env.has_math_range(block_name,loc,port):
            bound.append(var)
        else:
            free.append(var)

    return free,bound

def ival_derive_output_port(env,circ,block,config,loc,port):
    coeff = env.coeff(block.name,loc,port)
    dyn = block.get_dynamics(config.comp_mode,port)
    expr = ops.Mult(dyn,ops.Const(coeff))


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
    free,bound = bp_ival_hardware_classify_ports(env, variables)
    assert(len(free) == 0)
    free,bound = bp_ival_math_classify_ports(env, variables)
    for free_block_name,free_loc,free_port in free:
        free_block = circ.board.block(free_block_name)
        bp_derive_intervals(env,circ,free_block,\
                            circ.config(free_block.name,free_loc),\
                            free_loc,free_port)

    # compute intervals
    varmap = {}
    for var_block_name,var_loc,var_port in free+bound:
        ival = env.math_range(var_block_name,var_loc,var_port)
        varmap[var_port] = ival
        print("  v:%s=%s" % (var_port,ival))

    for handle in handles:
        ival = env.math_range(block.name, loc, port,
                               handle=handle)
        varmap[handle] = ival
        print("  h:%s=%s" % (handle,ival))

    intervals = expr.interval(varmap)

    if env.math_range(block.name,loc,port) is None:
        env.set_math_range(block.name,loc,port,intervals.interval)
        print("out %s[%s].%s => %s [c=%s]" % \
              (block.name,loc,port,intervals.interval,coeff))

    for handle,interval in intervals.bindings():
        if not env.math_range(block.name,loc,port,handle=handle):
            env.set_math_range(block.name,loc,port, \
                                interval,handle=handle)
            print("out %s[%s].%s:%s => %s" % \
                (block.name,loc,port,handle,interval))





def ival_derive_input_port(env,circ,block,config,loc,port):
    sources = list(circ.get_conns_by_dest(block.name,loc,port))
    free,bound = bp_ival_math_classify_ports(env,sources)
    print("input %s[%s].%s #srcs=%d" % (block.name,loc,port,len(sources)))
    assert(len(sources) > 0)
    for free_block_name,free_loc,free_port in free:
        free_block = circ.board.block(free_block_name)
        bp_derive_intervals(env,circ,free_block,
                            circ.config(free_block.name,free_loc),\
                            free_loc,free_port)

    expr_ival = None
    for src_block_name,src_loc,src_port in free+bound:
        src_ival = env.math_range(src_block_name,src_loc,src_port)
        expr_ival = src_ival if expr_ival is None else \
                    expr_ival.add(src_ival)

    env.set_math_range(block.name,loc,port,expr_ival)
    print("in %s[%s].%s => %s" % (block.name,loc,port,expr_ival))



def ival_derive_port(env,circ,block,config,loc,port):
    if block.is_input(port):
        ival_derive_input_port(env,circ,block,config,loc,port)

    elif block.is_output(port):
        ival_derive_output_port(env,circ,block,config,loc,port)

    else:
        raise Exception("what the fuck...")


def ival_port_to_range(block,config,port,handle=None):
    port_props = block.props(config.comp_mode,\
                            config.scale_mode,\
                            port,\
                            handle=handle)
    if isinstance(port_props,props.AnalogProperties):
        lb,ub,units = port_props.interval()
        return IRange(lb,ub)

    elif isinstance(port_props,props.DigitalProperties):
        lb = min(port_props.values())
        ub = max(port_props.values())
        return IRange(lb,ub)

    else:
        raise Exception("unhandled <%s>" % port_props)

def ival_hw_port_op_ranges(env,circ):

    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        mode = config.comp_mode
        for port in block.inputs + block.outputs:
            hwrng = ival_port_to_range(block,config,port)
            env.set_hardware_interval(block_name,loc,port,hwrng)
            for handle in block.handles(mode,port):
                hwrng = ival_port_to_range(block,config,port, \
                                              handle=handle)
                env.set_hardware_interval(block_name,loc,port,hwrng,\
                                          handle=handle)
def bp_bind_intervals(env,circ):
    # bind operating ranges for ports
    print("-> bind port operating ranges")
    ival_hw_port_op_ranges(env,circ)
    # bind math ranges of dacs
    print("-> bind math ranges of dac values")
    ival_math_dac_ranges(env,circ)
    # bind math ranges of labels
    print("-> bind math ranges of labels")
    ival_math_label_ranges(env,circ)
    print("-> derive intervals")
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for out_port in block.outputs:
            ival_derive_port(env,circ,block,config,loc,out_port)

    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for port in block.outputs + block.inputs:
            assert(env.has_hardware_range(block_name,loc,port))

def bp_bind_coefficients(env,circ):
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        for inp in block.inputs():
            scf = config.scf(inp)
            env.set_scf(block_name,loc,inp,scf)

        for out,expr in block.dynamics(config.comp_mode):
            coeff = block.coeff(config.comp_mode,\
                                     config.scale_mode,out)
            scf = config.scf(out)
            env.set_coeff(block_name,loc,out,coeff)
            env.set_scf(block_name,loc,out,scf)

def infer(circ):
  env= IntervalEnv()
  # declare scaling factors
  # pass1: fill intervals
  print("-> Derive + Bind Intervals")
  bp_bind_intervals(env,circ)

  # pass2: fill in hardware coefficients
  print("-> Fill Coefficients")
  bp_bind_coefficients(env,circ)

  return env
