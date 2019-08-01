from bmark.bmarks.columbia import \
        oscillator,vanderpol,\
        pendulum,spring,\
        robot_control,heat


def get_benchmarks():
  return [
    oscillator.model(),
    vanderpol.model(),
    pendulum.model(),
    pendulum.model(True),
    spring.model(),
    spring.model(True),
    robot_control.model(),
    heat.model(4,2),
    heat.model(4,2,with_gain=True),
    heat.model(9,2),
    heat.model(8,4),
    heat.model(8,4,with_gain=True),
    heat.model(17,9)
  ]
