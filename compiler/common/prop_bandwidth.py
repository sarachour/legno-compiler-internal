from compiler.common.visitor import Visitor
import chip.props as props
import ops.op as ops
from ops.interval import Interval, IRange, IValue


class PropBandwidthVisitor(Visitor):

  def __init__(self,prog,circ):
    Visitor.__init__(self,circ)
    self._prog = prog
    self.math_label_ranges()


  def math_label_ranges(self):
    prog,circ = self._prog,self.circ
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

                mbw = prog.bandwidth(label)
                config.set_bandwidth(port,mbw,handle=handle)



  def is_free(self,block_name,loc,port):
    config = self._circ.config(block_name,loc)
    return config.bandwidth(port) is None

  def input_port(self,block_name,loc,port):
    Visitor.input_port(self,block_name,loc,port)
    circ = self.circ
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    scf = config.scf(port) if config.has_scf(port) else 1.0
    dest_expr = ops.Const(0 if not config.has_dac(port) else \
                          config.dac(port)*scf)

    dest_bw = dest_expr.compute_bandwidth({}).bandwidth
    for src_block_name,src_loc,src_port in \
        circ.get_conns_by_dest(block_name,loc,port):
      src_config = circ.config(src_block_name,src_loc)
      src_bw = src_config.bandwidth(src_port)
      if(src_bw is None):
        print("free: <%s>\n" % free)
        print("bound: <%s>\n" % bound)

        raise Exception("unknown bandwidth: %s[%s].%s" % \
                        (src_block_name,src_loc,src_port))

      dest_bw = dest_bw.add(src_bw)

    config = circ.config(block.name,loc)
    config.set_bandwidth(port,dest_bw)
    #print("bw in %s[%s].%s => %s" % (block.name,loc,port,dest_bw))


  def output_port(self,block_name,loc,port):
    Visitor.output_port(self,block_name,loc,port)
    circ = self.circ
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    if not config.has_expr(port):
      expr = block.get_dynamics(config.comp_mode,port)
    else:
      expr = config.expr(port,inject=False)

    # compute intervals
    ival_map = config.intervals()
    bw_map = config.bandwidths()
    bandwidths = expr.infer_bandwidth(ival_map,bw_map)

    if config.bandwidth(port) is None:
      #print("bw %s[%s].%s = %s" % (block.name,loc,port,bandwidths.bandwidth))
      config.set_bandwidth(port,bandwidths.bandwidth)

    for handle,bandwidth in bandwidths.bindings():
      if not config.bandwidth(port,handle=handle):
        config.set_bandwidth(port,bandwidth,handle=handle)




def compute(prog,circ):
  PropBandwidthVisitor(prog,circ).all()
