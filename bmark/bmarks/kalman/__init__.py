from bmark.bmarks.kalman import constant, \
  freqdetect, \
  freqdetect_small, \
  freqdetect_simple

def get_benchmarks():
  return [
    constant.model(),
    freqdetect.model(),
    freqdetect_small.model(),
    freqdetect_simple.model()
  ]
