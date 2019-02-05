import ops.nop as nop
import ops.interval as interval

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
    return bw.timescale(self.circ.tau) \
             .timescale(1.0/self.circ.board.time_constant)

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

  def evaluate_expr(self,block_name,loc,port,expr,tag):
    variables = expr.vars()
    interval_dict = {}
    bandwidth_dict = {}
    ref_dict = {}
    for var in variables:
      block,inst = var.instance
      assert(not block is None)
      assert(not inst is None)
      port = var.port
      if var.op == nop.NOpType.FREQ:
        print("freq %s[%s].%s" % (block,inst,port))
        bandwidth_dict[(block,inst,port)] = self.freq(block,inst,port)

      elif var.op == nop.NOpType.SIG:
        print("sig %s[%s].%s" % (block,inst,port))
        interval_dict[(block,inst,port)] = self.interval(block,inst,port)

      elif var.op == nop.NOpType.REF:
        print("ref %s[%s].%s" % (block,inst,port))
        value = self.reference(block,inst,port,tag)
        if value is None:
          value = 0
        ref_dict[(block,inst,port)] = nop.mkconst(value)
      else:
        raise Exception("unknown")

    expr.concretize(ref_dict)
    result = expr.compute(bandwidth_dict, \
                        interval_dict)
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
    res_mean = interval.Interval.zero()
    res_variance = interval.Interval.zero()
    for freq_range,mean,variance in model.functions():
      if freq < freq_range.lower:
        self.set_reference(block_name,loc,port,'mean',
                           res_mean.bound)
        self.set_reference(block_name,loc,port,'variance',\
                           res_variance.bound)
        return res_mean,res_variance

      this_mean = self.evaluate_expr(block_name,loc,port, \
                                     mean,'mean')
      this_variance = self.evaluate_expr(block_name,loc,port, \
                                         variance,'variance')
      res_mean = res_mean.add(this_mean)
      res_variance = res_variance.add(this_variance)

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

  for _,m,v in model.functions():
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

  for _,m,v in model.functions():
    configure(m)
    configure(v)
