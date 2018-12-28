# Chip

1. there's no tile output 0.0.0.2.2
2. mult and dac also have value ranges, support m and l there
3. determine if ordering things has a significant impact
4. implement recalibrate statements for integ, mults, dacs
5. reduce maximum initial condition (1 is clearly not valid)
6. get to bottom of saturationissue.

# Bugs 

1. smmrxn / circuit 18. Two wires to multiplier 0.0.1.0.

# Compiler

1. bundle version of gpkit programmed to work with python3
2. Add support for f(t) inputs (special ast block)
3. investigate integrator scaling (what mode is default?)
4. what other components have scaling?

# Paper Contribution List

1. Noise Model Composition Analysis (Infer Noise Model Block From Other Block)
2. Input Signal Inference (wishlist)
3. Modelling Language for Signal dependent/independent noise
4. Basic Model Inference Algorithm

# Lab Bench

1. add support for pluggable reference functions. I.e. if you connect A to B, compute the reference function.

2. trim time-series signal to exclude transient behavior at start/end

3. factor out input signal generation. general process: (1) execute with seed signals (2) compute noise model (3) generate additional inputs to refine noise.

4. what do we need from noise model. In DAC there is clear input dependence for noise amplitude/bias.

5. integrate analysis to prevent file glut. (use emp-data from_json). Emit frequency information of inputs, output, reference, noise and phase information.

6. write ifft to reconstruct signal from frequency information.

7. use info ben sent me to remove negative frequency phase|amplitude/negative amplitude 

8. different model representations. spike bloom function (assumes no frequency band corrleations).

# Chip / Voltage Divider 

1. Improve noise characteristics of voltage divider. DONE

2. Derive reference function for voltage divider from schematic description. DONE

3. Bayesian Inference

# Chip / Constant DAC

1. Flash configurations for reading DAC values. DONE
2. Use oscilloscope to quantify DAC noise
3. Use DUE ADCs to quantify DUE ADC noise
4. Flash configurations for reading multiplier. DONE
5. Flash 


# Hardware Model Errata

 - Cannot use DAC in same slice if mult is in use.
 - Multiplier does not support signal inversion
 - Constant value is two sided for DAC and ADC. Flipping DAC flips sign, but doesn't confer any benefits computationally.
 - 
