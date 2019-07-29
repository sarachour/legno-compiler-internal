from bmark.bmarks.kalman import constant,freqdetect,freqdetect2

def get_benchmarks():
  return [
    constant.model(),
    freqdetect.model(),
    freqdetect2.model()
  ]
