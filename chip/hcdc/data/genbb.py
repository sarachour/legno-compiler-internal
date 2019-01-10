import sys


filename = sys.argv[1]

header = [
  'freq','ampl_mu_mv','ampl_mu_pct', \
  'ampl_std_mv','ampl_std_pct', \
  'rms_mu_mv','rms_mu_pct', \
  'rms_computed', 'phase_rad', \
  'shift_rad', 'shift_deg', \
  'phase_std_rad', \
  'phase_std_pct'
]
rawdata = {
  'freqs': [],
  'ampl_mu': [],
  'ampl_std': [],
  'delay_mu': [],
  'delay_std': [],
}
n = 0

with open(filename,'r') as fh:
  fh.readline()
  for row in fh:
    args = row.strip().split(",")
    assert(len(args) == len(header))
    if args[0] == '':
      continue

    datum = dict(zip(header,map(lambda a: float(a), args)))
    rawdata['freqs'].append(datum['freq'])
    rawdata['delay_mu'].append(datum['shift_rad'])
    rawdata['delay_std'].append(datum['phase_std_rad'])
    rawdata['ampl_mu'].append(datum['ampl_mu_mv'])
    rawdata['ampl_std'].append(datum['ampl_std_mv'])
    n += 1

data = {
  'ampl_bias_indep': [],
  'ampl_noise_indep': [],
  'ampl_bias_dep': [],
  'ampl_noise_dep': [],
  'delay_mean': [],
  'delay_std': []
}

max_ampl = max(rawdata['ampl_mu'])
bias_corr_split = 0.01
noise_corr_split = 0.3
for idx in range(len(rawdata['freqs'])):
  freq = rawdata['freqs'][idx]
  bias = rawdata['ampl_mu'][idx] - max_ampl
  bias_uncorr = bias_corr_split*bias
  bias_corr = ((1.0-bias_corr_split)*bias)/max_ampl

  noise = rawdata['ampl_std'][idx]
  noise_uncorr = noise_corr_split*noise
  noise_corr = ((1.0-noise_corr_split)*noise)/max_ampl

  delay_mu = rawdata['delay_mu'][idx]
  delay_std = rawdata['delay_std'][idx]

  data['ampl_bias_indep'].append(bias_uncorr)
  data['ampl_bias_dep'].append(bias_corr)
  data['ampl_noise_indep'].append(noise_uncorr)
  data['ampl_noise_dep'].append(noise_corr)
  data['delay_mean'].append(delay_mu)
  data['delay_std'].append(delay_std)

print("TODO: infer model")

