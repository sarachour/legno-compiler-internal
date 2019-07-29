import bmark.bmarks.kalman.constant as constant
import bmark.bmarks.kalman.freqdetect as freqdetect
import bmark.bmarks.kalman.freqdetect2 as freqdetect2

def get_benchmarks():
  return [
    constant.model(),
    freqdetect.model(),
    freqdetect2.model()
  ]
