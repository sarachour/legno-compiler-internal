# Running Questions

1. I connected a mic with a dynamic range of 2.0 V (-1.0V to 1.0V) to the input pins, then directly routed the pins using interconnects to the external output ADC. The dynamic range of the corresponding differential signal is 3.3 V (-1.6-1.6 V). This is different from what is reported in the documentation (-1.3-1.3 V). Why? 

# Benchmark Status

- vanderpol and sin require low-freq

## Subsets

sets of parameters

#### Subsets
standard = only the medium components
extended = enables integrator hm
extended2 = extended + integrator mh, hm, and dac+fan h
unrestricted = everything

#### Models 
ideal = no minimum value constraints
naive = assumes gain is 1.0, oprange is 1.0, uncertainty is 0.01 
physical = minimum value constraints + quantization constraints

#### limitations:
- no adc for now (does dividing by 2 on input work?)
- spring/pendulum are linear
- max freq: 40 khz (tau*time constant)
- subset of components that are well characterized. Working on enabling full set of modes.

#### benchmarks:
- spring, pend, cosc, vanderpol


# TODO list

- BUG: lotka can't scale up gain for multiplier going to output
- BUG: spring has issues with conservation.

# Calibration Failures

use_integ 0 0 0 sgn + val 0.900000 rng m l debug update
use_integ 0 0 0 sgn + val 0.900000 rng l l debug update
use_integ 0 0 0 sgn + val 0.900000 rng l m debug update
use_adc 0 0 0 rng m update



1. ADC Issues Update: the ADC does not update with time. Use Simple-Osc with an ADC to test it with time varying signals.
   - 1.0*in = ic*2
   - 0.5*in = ic
   - 0 = 0
   - tested with time varying external function. Does not vary (stuckat 1)
     - moved other components to different slice. no effect.
     - moved other components to different tile. no effect.
     - todo: move components to different chip? look at reference code?
 
# Enumeration of Contributions

## Compiler

#### Arco
- computational mode selection
- component types (copiers, computation, buses)
- bus components resolved at lower level.
- current mode - kirchoff's rule, need copiers
- voltage mode - unlimited fanout, need adders

#### Jaunt
- scaling mode selection
- handle transfer function gains
- minimum signal constraints, quantization constraints (resolution).
- seamless integration of physical model.
- bandwidth constraints

#### Srcgen
- low-level language, interpreter.
- use naive models, physical models from hardware.

#### Key result
- able to compile simulations to chip, recover original dynamics.

## Profiling and Simulator Production

#### Conceptual

- calibration -> global optimization to minimize error between specification and behavior.
   - divide parameter space into $p_{hidden}$ and $p_{compiler}$, the compiler parameters are set by compiler, the hidden parameters are resolved during calibration. Anything with predictable static behavior should be set at compile time.
   - build model per $p_{compiler}$ instance.
   
- profiling -> gather data that characterizes gap between specification and behavior.
   - potentially expensive.
   - designers should consider how much of the unexpected behavior of the chip is externally profilable. 
   
- model inference -> build conceptual model between specification and behavior. Any unmodelable behavior is uncertainty.
   - model inference is useful for validating ones own understanding of the hardware platform. Hardware designers choose a model that makes sense, given the physics of the platform. Any block that is poorly adhering to this model may need a hardware redesign/have calibration bug.

- benefits of model inference: build space of models from blocks in a prototype, sample from model space to produce random hardware platforms. Automatically incorporate model in simulator.

#### Artifacts

- data elicitation engine. Chooses next set of points, given current knowledge. Especially useful for multipliers.
     - grendel -> uses profiling to bridge gap between chip specification and behavior, chooses points to maximize information gained for model.

- model inference engine: Infers model from data.

- analog chip simulator: simulation platform for analog chip.

- apply physics model to hardware specification.

#### Key results

- simulator adheres to hardware behavior on test points (not trained on).


#### Srcgen
- grendel profiling.

#### Key result
- able to get better simulation results, recover original dynamics.

# Enumeration of Contributions:

## Calibration

 - question, for scaling down, what is the appropriate error? It is not converging as is. Maybe test this?

 - calibration / profiling loop for building parameter dataset.
   - empirical analysis (noise is low, bias can be significant)
   - found bugs with analog hardware guy's calibration routine. (nonlinear multiplier bug)
   - 
   - offline predictive techniques (TODO??)
   
 - *if necessary*: bias correction technique. 
