from compiler.common.visitor import Visitor
import chip.props as props
import ops.op as ops
import ops.nop as nop
import compiler.common.base_propagator_symbolic as propagate
import compiler.common.data_symbolic as symdata

from ops.interval import Interval, IRange, IValue


class PropSNRVisitor(Visitor):

  def __init__(self,prog,circ):
    Visitor.__init__(self,circ)
    self._prog = prog
    self.default_snr = prog.default_snr()
    self.math_label_ranges()

  def math_label_ranges(self):
    prog,circ = self._prog,self.circ
    for block_name,loc,config in circ.instances():
        block = circ.board.block(block_name)
        if not block_name == 'integrator' and \
           not block_name == 'ext_chip_in':
          continue

        for port in block.outputs + block.inputs:
            if config.has_label(port):
                label = config.label(port)
                if port in block.outputs:
                    handle = block.get_dynamics(config.comp_mode,\
                                                port).toplevel()
                else:
                    handle = None

                snr = prog.snr(label)
                config.set_snr(port,snr)
            else:
              config.set_snr(port,self._prog.default_snr())


  def is_free(self,block_name,loc,port):
    config = self._circ.config(block_name,loc)
    return config.snr(port) is None

  def input_port(self,block_name,loc,port):
    Visitor.input_port(self,block_name,loc,port)
    circ = self._circ
    config = circ.config(block_name,loc)
    interval = config.interval(port)

    snrs = []
    n_inps = 0
    for src_block_name,src_loc,src_port in \
        circ.get_conns_by_dest(block_name,loc,port):
      src_config = circ.config(src_block_name,src_loc)
      src_snr = src_config.snr(src_port)
      snrs.append(src_snr)
      n_inps += 1

    if n_inps == 0:
      snr = self.default_snr
    else:
      snr = max(snrs)

    print("snr in %s[%s].%s => %s" % (block_name,loc,port,snr))
    config.set_snr(port,snr)


  def _update_snrs(self,block_name,loc,port):
    circ = self._circ
    block = circ.board.block(block_name)
    config = circ.config(block_name,loc)
    # don't apply any coefficients
    if not config.has_expr(port):
      expr = block.get_dynamics(config.comp_mode,port)
    else:
      expr = config.expr(port,inject=False)

    snrmap = config.snrs()
    snrs = []
    for var in expr.vars():
      snrs.append(snrmap[var])

    if block_name == 'integrator':
      return

    snr = max(snrs)
    print("snr out %s[%s].%s => %s" % (block_name,loc,port,snr))
    config.set_snr(port,snr)


  def output_port(self,block_name,loc,port):
    Visitor.output_port(self,block_name,loc,port)
    self._update_snrs(block_name,loc,port)


def compute_snrs(prog,circ):
  visitor = PropSNRVisitor(prog,circ)
  visitor.all()

