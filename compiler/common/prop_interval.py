from compiler.common.visitor import Visitor
import chip.props as props
import ops.op as ops
from ops.interval import Interval, IRange, IValue

class PropIntervalVisitor(Visitor):

  def __init__(self,prog,circ):
    Visitor.__init__(self,circ)
    self._prog = prog
    self.hardware_op_ranges()
    self.math_label_ranges()

  def hardware_op_ranges(self):
    def ival_port_to_range(block,config,port,handle=None):
      assert(not config.scale_mode is None)
      assert(not config.comp_mode is None)
      return block.props(config.comp_mode,\
                         config.scale_mode,\
                         port,\
                         handle=handle).interval()

    '''main body '''
    circ = self.circ
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


  def math_label_ranges(self):
    prog,circ = self._prog,self.circ
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        if not block_name == 'integrator':
          continue

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
                print("lbl: %s[%s].%s := %s" % \
                      (block_name,loc,port,mrng))

                config.set_interval(port,mrng,\
                                    handle=handle)
                config.set_bandwidth(port,mbw,\
                                    handle=handle)



  def is_free(self,config,variable):
    return config.interval(variable) is None \
            or config.interval(variable).unbounded()

  def input_port(self,block_name,loc,port):
    Visitor.input_port(self,block_name,loc,port)
    circ = self._circ
    config = circ.config(block_name,loc)
    dest_expr = ops.Const(0.0 if not config.has_dac(port) \
                          else config.dac(port))
    dest_ival = dest_expr.compute_interval({}).interval

    for src_block_name,src_loc,src_port in \
        circ.get_conns_by_dest(block_name,loc,port):
      src_config = circ.config(src_block_name,src_loc)
      src_ival = src_config.interval(src_port)
      if(src_ival is None):
        print("free: <%s>\n" % free)
        print("bound: <%s>\n" % bound)

        raise Exception("unknown interval: %s[%s].%s" % \
                        (src_block_name,src_loc,src_port))

      dest_ival = dest_ival.add(src_ival)

    config.set_interval(port,dest_ival)
    print("ival in %s[%s].%s => %s" % (block_name,loc,port,dest_ival))

  def _update_intervals(self,block_name,loc,port):
    circ = self._circ
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    # don't apply any coefficients
    expr = block.get_dynamics(config.comp_mode,port, \
                              scale_mode=None)

    intervals = expr.compute_interval(config.intervals())
    config.set_interval(port,intervals.interval)
    print("ival out %s[%s].%s => %s" % (block_name,loc,port,intervals.interval))

    for handle,interval in intervals.bindings():
      config.set_interval(port, \
                          interval,handle=handle)



  def output_port(self,block_name,loc,port):
    self._update_intervals(block_name,loc,port)
    Visitor.output_port(self,block_name,loc,port)
    self._update_intervals(block_name,loc,port)

  def is_valid(self):
    circ = self._circ
    valid = True
    for block_name,loc,config in circ.instances():
      for ival in config.intervals().values():
        if ival.unbounded():
           valid = False
    return valid

def compute(prog,circ):
  visitor = PropIntervalVisitor(prog,circ)
  visitor.all()
  while(not visitor.is_valid()):
      print("-> recomputing intervals");
      visitor.clear()
      visitor.all()
