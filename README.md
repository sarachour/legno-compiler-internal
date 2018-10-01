# leto-compiler
compilation tools for automated analog configuration generation


**leto**: Leto is the toplevel compiler. This compiler returns a sequence of algebraically equivalent configurations of the dynamical system. Leto will eventually perform the following compiler optimizations:

   - uses rewrite rules to transform the dynamical system and render it more amenable to produce low-noise configurations.
   - transforms parameters and time so resulting simulation executes within hardware operating ranges, while also optimizing for speed and noise.
   - ranks configurations by how likely they are to be noisy.
   - generates projects for executing experiments on the arduino.
   
**apep**: Apep is small tool that generates projects for calibration procedures.

**scripts/save_data.py**: a client side script that records the data from the experiment as it's running.

**scripts/read_data.py**: extracts the data recorded from the arduino into data files.

**scripts/visualize.py**: renders the extracted data as a plot.


