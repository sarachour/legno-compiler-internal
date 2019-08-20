from bmark.bmarks.kalman import  \
  constant_detect, \
  water, \
  water_influx, \
  water_leak, \
  amplitude_modulate, \
  freq_modulate, \
  phase_match, \
  amplitude_detect_square, \
  amplitude_detect_cos

def get_benchmarks():
  return [
    # don't know
    amplitude_modulate.model(),
    freq_modulate.model(),
    phase_match.model(),
    # works
    constant_detect.model(),
    amplitude_detect_square.model(),
    amplitude_detect_cos.model(),
    water.model(),
    # doesn't work
    water_influx.model(),
    water_leak.model(),
    # deprecated
    #freqdetect.model(),
    #freqdetect_small.model(),
    #freqdetect_simple.model()
  ]
