import bmark.bmarks.columbia.oscillator as oscillator
import bmark.bmarks.columbia.vanderpol as vanderpol
import bmark.bmarks.columbia.pendulum as pendulum
import bmark.bmarks.columbia.spring as spring
import bmark.bmarks.columbia.robot_control as robot_control
import bmark.bmarks.columbia.heat as heat


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
    heat.model(8,4),
    heat.model(8,4,with_gain=True),
    heat.model(17,9)
  ]
