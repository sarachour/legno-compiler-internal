
import chip.hcdc.energy_model as energy_model

def analyze(entry,conc_circ):
  energy = energy_model.compute_energy(conc_circ,entry.runtime)
  entry.set_energy(energy)
