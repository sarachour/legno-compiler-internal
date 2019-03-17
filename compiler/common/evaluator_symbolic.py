import ops.nop as nop
import ops.interval as interval
import ops.bandwidth as bandwidth

class Evaluator:
  def __init__(self,circ,func,config_func=None):
    self._circ = circ
    self._refs = {}
    self._func = func
    self._config_func = config_func
    # evaluate to get propagation refs
    self._evaluate()
    # evaluate to substitute propagation refs
    self._evaluate()

  @property
  def circ(self):
    return self._circ


  def freq(self,block_name,loc,port):
    bw = self.circ.config(block_name,loc).bandwidth(port)
    scbw = bw.timescale(self.circ.tau)
    return scbw

  def interval(self,block_name,loc,port):
    interval = self.circ.config(block_name,loc).interval(port)
    scf = self.circ.config(block_name,loc).scf(port)
    return interval.scale(scf)


  def reference(self,block_name,loc,port,tag):
    if not (block_name,loc,port,tag) in self._refs:
      return None

    return self._refs[(block_name,loc,port,tag)]

  def set_reference(self,block_name,loc,port,tag,expr):
    self._refs[(block_name,loc,port,tag)] = expr

  def compute_bindings(self,expr,tag):
    variables = expr.vars()
    interval_dict = {}
    ref_dict = {}
    freq_dict = {}
    for var in variables:
      block,inst = var.instance
      assert(not block is None)
      assert(not inst is None)
      port = var.port
      if var.op == nop.NOpType.FREQ:
        bw = self.freq(block,inst,port)
        freq_dict[(block,inst,port)] = bw

      elif var.op == nop.NOpType.SIG:
        ival = self.interval(block,inst,port)
        interval_dict[(block,inst,port)] = ival

      elif var.op == nop.NOpType.REF:
        ref_dict[(block,inst,port)] = nop.mkzero()

      else:
        raise Exception("unknown")

    return ref_dict,interval_dict,freq_dict

  def evaluate_expr(self,block_name,loc,port,expr,tag):
    ref_dict,interval_dict,freq_dict = self.compute_bindings(expr,tag)
    expr.concretize(ref_dict)
    # test to see if this is in range.
    result = expr.compute(freq_dict, \
                          interval_dict)
    if result.unbounded():
      raise Exception("unbounded: %s" % result)
    assert(not result is None)
    return result

  def _evaluate_port(self,block_name,loc,port):
    config = self.circ.config(block_name,loc)
    func = getattr(config,self._func)
    model = getattr(config,self._func)(port)
    if model is None:
      return

    if not self._config_func is None:
      self._config_func(model)

    freq = self.freq(block_name,loc,port).fmax
    mean,variance = model.mean,model.variance
    this_mean = self.evaluate_expr(block_name,loc,port, \
                                   mean,'mean')
    this_variance = self.evaluate_expr(block_name,loc,port, \
                                       variance,'variance')

    res_mean = this_mean
    res_variance = this_variance

    fmax = self.freq(block_name,loc,port).bandwidth
    self.set_reference(block_name,loc,port,'mean',
                       res_mean.bound)
    self.set_reference(block_name,loc,port,'variance',\
                       res_variance.bound)


  def _evaluate(self):
    for block_name,loc,_ in self._circ.instances():
      block = self._circ.board.block(block_name)
      for port in block.inputs:
        self._evaluate_port(block_name,loc,port)
        mean = self.reference(block_name,loc,port,'mean')
        vari = self.reference(block_name,loc,port,'variance')

      for port in block.outputs:
        self._evaluate_port(block_name,loc,port)
        mean = self.reference(block_name,loc,port,'mean')
        vari = self.reference(block_name,loc,port,'variance')


  def get(self,block,loc,port):
    mean = self.reference(block,loc,port,'mean')
    variance = self.reference(block,loc,port,'variance')
    return mean,variance

class DelayEvaluator(Evaluator):
  def __init__(self,circ):
    Evaluator.__init__(self,circ)

  def get_model(self,block_name,loc,port):
    expr = self.circ.config(block_name,loc) \
                   .generated_delay(port)
    return expr


def evaluate(circ,block_name,loc,port,model):
  return Evaluator(circ) \
    .evaluate(block_name,loc,port,model)

def generated_bias_evaluator(circ):
  return Evaluator(circ,func='generated_bias')


def generated_noise_evaluator(circ):
  return Evaluator(circ,func='generated_noise')


def generated_delay_evaluator(circ):
  return Evaluator(circ,func='generated_delay')

def propagated_bias_evaluator(circ):
  return Evaluator(circ,func='propagated_bias')


def propagated_noise_evaluator(circ):
  return Evaluator(circ,func='propagated_noise')

def propagated_delay_evaluator(circ):
  return Evaluator(circ,func='propagated_delay',
                   config_func=configure_propagated_delay)



def delay_mismatch_evaluator(circ):
  return Evaluator(circ,func='propagated_delay',
                   config_func=configure_mismatch)



def configure_propagated_delay(model):
  def configure(e):
    if e.op == nop.NOpType.SEL:
      e.set_mode(nop.NSelect.Mode.MAX)

    for arg in e.args():
      configure(arg)

  m,v = model.mean,model.variance
  configure(m)
  configure(v)



def configure_mismatch(model):
  def configure(e,mismatch=True):
    new_mismatch = mismatch
    if e.op == nop.NOpType.SEL:
      if mismatch:
        e.set_mode(nop.NSelect.Mode.DIFF)
        new_mismatch = False
      else:
        e.set_mode(nop.NSelect.Mode.MAX)

    for arg in e.args():
      configure(arg,mismatch=new_mismatch)

  m,v = model.mean,model.variance
  configure(m)
  configure(v)



