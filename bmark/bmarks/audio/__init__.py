import bmark.bmarks.audio.lpf as audio_lpf
import bmark.bmarks.audio.bpf as audio_bpf
import bmark.bmarks.audio.passthru as audio_passthru
import bmark.bmarks.audio.kalman as audio_kalman


def get_benchmarks():
  return [
    audio_lpf.model(1,"basic"),
    audio_lpf.model(2,"basic"),
    audio_lpf.model(3,"chebychev"),
    audio_lpf.model(3,"butter"),
    audio_kalman.model(),
    audio_passthru.model()

  ]
