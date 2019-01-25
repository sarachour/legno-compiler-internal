import numpy as np
import ops.bandwidth as bandwidth
import ops.interval as interval

def compute_delay(phys,output,freqs,intervals):
  freq = freqs[output].bandwidth
  delay_deg = phys.delay(freq).compute(freqs,intervals)
  if freq == 0:
    return interval.Interval.type_infer(0,0)

  return delay_deg.scale(1.0/(360*freq))

def compute_bias(phys,output,freqs,intervals,n=5):
  bias = interval.Interval.type_infer(0,0)
  freq = freqs[output].bandwidth
  seg_ivals = dict(map(lambda args: \
                       (args[0],args[1].scale(1.0/max(1.0,freq))),
                   intervals.items()))

  for (fmin,fmax),expr in phys.bias(freq):
    fs = []
    ls = []
    us = []
    for freq in np.linspace(fmin,fmax,n):
      fs.append(freq)
      bw = bandwidth.Bandwidth(freq)
      seg_freqs = dict(map(lambda args: (args[0],\
                                         bw),\
                           freqs.items()))
      nz = expr.compute(seg_freqs,seg_ivals)
      ls.append(nz.lower)
      us.append(nz.upper)

    upper_auc = np.trapz(us,fs)
    lower_auc = np.trapz(ls,fs)
    auc = interval.Interval.type_infer(lower_auc,upper_auc)
    auc_norm = auc.scale(1.0/max(1.0,freq))
    bias = bias.add(auc_norm)

  return bias


def compute_noise(phys,output,freqs,intervals,n=5):
  noise = interval.Interval.type_infer(0,0)
  freq = freqs[output].bandwidth
  seg_ivals = dict(map(lambda args: \
                       (args[0],args[1].scale(1.0/max(1.0,freq))),
                   intervals.items()))

  for (fmin,fmax),expr in phys.noise(freq):
    fs = []
    ls = []
    us = []
    for freq in np.linspace(fmin,fmax,n):
      fs.append(freq)
      bw = bandwidth.Bandwidth(freq)
      seg_freqs = dict(map(lambda args: (args[0],\
                                         bw),\
                           freqs.items()))
      nz = expr.compute(seg_freqs,seg_ivals)
      ls.append(nz.lower)
      us.append(nz.upper)

    upper_auc = np.trapz(us,fs)
    lower_auc = np.trapz(ls,fs)
    auc = interval.Interval.type_infer(lower_auc,upper_auc)
    auc_norm = auc.scale(1.0/max(freq,1.0))
    noise = noise.add(auc_norm)

  return noise

def compute(circ):
  period = circ.tau*circ.board.time_constant
  for blk_name,loc,config in circ.instances():
    block = circ.board.block(blk_name)
    freqs = config.bandwidths(time_constant=circ.board.time_constant)
    intervals = config.intervals()
    for output in block.outputs:
      print("%s[%s].%s" % (blk_name,loc,config))
      print(blk_name,output)
      phys = config.physical(block,output)
      freq = freqs[output].bandwidth
      delay = compute_delay(phys,output,freqs,intervals)
      noise = compute_noise(phys,output,freqs,intervals)
      bias = compute_bias(phys,output,freqs,intervals)
      print("noise: %s" % noise)
      print("bias: %s" % noise)
      print("delay: %s" % noise)

      config.set_generated_noise(output,noise)
      config.set_generated_bias(output,bias)
      config.set_generated_delay(output,delay)


