from bmark.bmarks.audio import lpf, bpf,passthru,kalman


def get_benchmarks():
  return [
    lpf.model(1,"basic"),
    lpf.model(2,"basic"),
    lpf.model(3,"chebychev"),
    lpf.model(3,"butter"),
    kalman.model(),
    passthru.model()

  ]
