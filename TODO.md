# TODO
# TODO List

0. micro-osc-quarter, micro-osc-quad, vanderpol all work

1. the LUT flips signs (see the writeLut function for correction). How exactly is it flipping the signs? Is it the input? the output? try different tests.

2. test spring and pend (until they're working again).

3. try heat1d

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
