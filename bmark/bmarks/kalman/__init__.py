import bmark.bmarks.kalman.constant as constant
import bmark.bmarks.kalman.freqdetect as freqdetect

def get_benchmarks():
  return [
    constant.model(),
    freqdetect.model()
  ]
