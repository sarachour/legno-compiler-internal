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
    spring.model(),
    #robot_control.model(),
    heat.model(2,1),
    heat.model(4,2),
  ]
