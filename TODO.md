# Running Questions

1. I connected a mic with a dynamic range of 2.0 V (-1.0V to 1.0V) to the input pins, then directly routed the pins using interconnects to the external output ADC. The dynamic range of the corresponding differential signal is 3.3 V (-1.6-1.6 V). This is different from what is reported in the documentation (-1.3-1.3 V). Why? 

# TODO List

can't calibrate:

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
   
3. heat1d/2:

4. try repri, gentoggle.

# Enumeration of Contributions:

## Calibration

 - question, for scaling down, what is the appropriate error? It is not converging as is. Maybe test this?

 - calibration / profiling loop for building parameter dataset.
   - empirical analysis (noise is low, bias can be significant)
   - found bugs with analog hardware guy's calibration routine. (nonlinear multiplier bug)
   - 
   - offline predictive techniques (TODO??)
   
 - *if necessary*: bias correction technique. 
