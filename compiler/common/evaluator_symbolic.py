import ops.nop as nop
import ops.interval as interval

class Evaluator:
  def __init__(self,circ):
    self._circ = circ

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


  def evaluate_expr(self,expr):
    variables = expr.vars()
    interval_dict = {}
    bandwidth_dict = {}
    for var in variables:
      block,inst = var.instance
      assert(not block is None)
      assert(not inst is None)
      port = var.port
      if var.op == nop.NOpType.FREQ:
        print("freq %s[%s].%s" % (block,inst,port))
        bandwidth_dict[(block,inst,port)] = self.freq(block,inst,port)

      elif var.op == nop.NOpType.SIG:
        print("sig  %s[%s].%s" % (block,inst,port))
        interval_dict[(block,inst,port)] = self.interval(block,inst,port)

      else:
        raise Exception("unknown")

    return expr.compute(bandwidth_dict, \
                        interval_dict)

  def evaluate(self,block_name,loc,port,model):
    freq = self.freq(block_name,loc,port).fmax
    res_mean = interval.Interval.zero()
    res_variance = interval.Interval.zero()
    for freq_range,mean,variance in model.functions():
      if freq < freq_range.lower:
        return res_mean,res_variance

      this_mean = self.evaluate_expr(mean)
      this_variance = self.evaluate_expr(variance)
      res_mean = res_mean.add(this_mean)
      res_variance = res_variance.add(this_variance)

    return res_mean,res_variance

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

def evaluate_generated_bias(circ,block_name,loc,port):
  return evaluate(circ,block_name,loc,port, \
                  circ.config(block_name,loc).generated_bias(port))


def evaluate_generated_noise(circ,block_name,loc,port):
  return evaluate(circ,block_name,loc,port, \
                  circ.config(block_name,loc).generated_noise(port))


def evaluate_generated_delay(circ,block_name,loc,port):
  return evaluate(circ,block_name,loc,port, \
                  circ.config(block_name,loc).generated_delay(port))

def evaluate_propagated_bias(circ,block_name,loc,port):
  return evaluate(circ,block_name,loc,port, \
                  circ.config(block_name,loc).propagated_bias(port))


def evaluate_propagated_noise(circ,block_name,loc,port):
  return evaluate(circ,block_name,loc,port, \
                  circ.config(block_name,loc).propagated_noise(port))



def evaluate_propagated_delay(circ,block_name,loc,port):
  def configure(e):
    if e.op == nop.NOpType.SEL:
      e.set_mode(nop.NSelect.Mode.MAX)

    for arg in e.args():
      configure(arg)

  model = circ.config(block_name,loc).propagated_delay(port)
  for _,m,v in model.functions():
    configure(m)
    configure(v)

  return evaluate(circ,block_name,loc,port,model)



def evaluate_delay_mismatch(circ,block_name,loc,port):
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

  model = circ.config(block_name,loc).propagated_delay(port)
  for _,m,v in model.functions():
    configure(m)
    configure(v)

  return evaluate(circ,block_name,loc,port,model)
