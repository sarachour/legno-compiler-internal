# TODO
# TODO List


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
