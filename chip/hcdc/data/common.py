import sys
import os
import pwlf
import numpy as np
import matplotlib.pyplot as plt

def load_raw_data(filename):
  header = [
    'freq','ampl_mu_mv','ampl_mu_pct', \
    'ampl_std_mv','ampl_std_pct', \
    'rms_mu_mv','rms_mu_pct', \
    'rms_computed', 'phase_rad', \
    'shift_rad', 'shift_deg', \
    'phase_std_rad', \
    'phase_std_pct'
  ]
  raw_data = {
    'freqs': [],
    'ampl_mu': [],
    'ampl_std': [],
    'delay_mu': [],
    'delay_std': [],
  }
  print("=== Reading Raw Data ===")
  with open(filename,'r') as fh:
    fh.readline()
    for row in fh:
      args = row.strip().split(",")
      assert(len(args) == len(header))
      if args[0] == '':
        continue

      datum = dict(zip(header,map(lambda a: float(a), args)))
      raw_data['freqs'].append(datum['freq'])
      raw_data['delay_mu'].append(datum['shift_rad'])
      raw_data['delay_std'].append(datum['phase_std_rad'])
      raw_data['ampl_mu'].append(datum['ampl_mu_mv'])
      raw_data['ampl_std'].append(datum['ampl_std_mv'])

  return raw_data

def process_raw_data(raw_data):
  data = {
    'ampl_bias_indep': [],
    'ampl_noise_indep': [],
    'ampl_bias_dep': [],
    'ampl_noise_dep': [],
    'delay_mean': [],
    'delay_std': []
  }

  max_ampl = max(raw_data['ampl_mu'])
  bias_corr_split = 0.01
  noise_corr_split = 0.3
  print("=== Inferring Data to Fit ===")
  for idx in range(len(raw_data['freqs'])):
    freq = raw_data['freqs'][idx]
    bias = raw_data['ampl_mu'][idx] - max_ampl
    bias_uncorr = bias_corr_split*bias
    bias_corr = ((1.0-bias_corr_split)*bias)/max_ampl

    noise = raw_data['ampl_std'][idx]
    noise_uncorr = noise_corr_split*noise
    noise_corr = ((1.0-noise_corr_split)*noise)/max_ampl

    delay_mu = raw_data['delay_mu'][idx]
    delay_std = raw_data['delay_std'][idx]

    data['ampl_bias_indep'].append(bias_uncorr)
    data['ampl_bias_dep'].append(bias_corr)
    data['ampl_noise_indep'].append(noise_uncorr)
    data['ampl_noise_dep'].append(noise_corr)
    data['delay_mean'].append(delay_mu)
    data['delay_std'].append(delay_std)

  return data


def plot_pwl(X,Y,model):
  #slopes = do_fit.slopes
  #offsets = do_fit.beta
  YH = model.predict(X)
  plt.scatter(X,Y,label='data')
  plt.plot(X,YH,label='fit')
  plt.savefig('fit.png')
  plt.clf()
  input()


def compute_pwls(X,data,n=3,extern_breaks=None):

  all_breaks = []
  pwls = {}
  for field in data.keys():
    print("==== %s ====" % field)
    Y = data[field]
    do_fit = pwlf.PiecewiseLinFit(X,Y,sorted_data=True)
    if extern_breaks is None:
      breaks = do_fit.fit(n)
      all_breaks += list(breaks)
    else:
      do_fit.fit_with_breaks(extern_breaks)
      breaks = extern_breaks

    print(breaks)
    pwls[field] = {
      'slopes': do_fit.calc_slopes(),
      'offsets': do_fit.predict(breaks[:-1]),
      'breaks': breaks,
      'model':do_fit
    }


  return all_breaks,pwls
