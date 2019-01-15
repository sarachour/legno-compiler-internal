
def compute(circ):
  period = circ.tau*circ.board.time_constant
  for blk_name,loc,config in circ.instances():
    block = circ.board.block(blk_name)
    freqs = config.bandwidths(time_constant=circ.board.time_constant)
    intervals = config.intervals()
    for output in block.outputs:
      print("%s[%s].%s" % (blk_name,loc,config))
      phys = config.physical(block,output)
      freq = freqs[output].bandwidth
      print("freq: %s" % freq)
      print("noise: %s" % phys.noise(freq))
      delay = phys.delay(freq).compute(freqs,intervals)
      noise = phys.noise(freq).compute(freqs,intervals)
      bias = phys.bias(freq).compute(freqs,intervals)
      config.set_generated_noise(output,noise)
      config.set_generated_bias(output,bias)
      config.set_generated_delay(output,delay)

