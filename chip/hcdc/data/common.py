import sys
import os
import pwlf
import numpy as np
import matplotlib.pyplot as plt
import scipy

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


def plot_pwl(name,X,Y,model):
  #slopes = do_fit.slopes
  #offsets = do_fit.beta
  YH = model.predict(X)
  plt.scatter(X,Y,label='data')
  plt.plot(X,YH,label='fit')
  plt.savefig(name)
  plt.clf()

def breaks_posy(fmax,n):
  divs = np.linspace(0,fmax,n+1)[:-1]
  return divs

def predict_posy(pdict,maxf,f,n):
  divs = breaks_posy(maxf,n)
  def compute_value(f,i):
    get = lambda name : pdict['%s[%d]' % (name,i)]

    x,y = get('x'),get('y')
    u,v = get('u'),get('v')
    w = get('w')

    value = x*(f**u) + y*(f**(-1*v)) + w
    return value

  def freq_break(i):
    bsc = pdict['bsc']
    return divs[i]*bsc

  def compute_first(f,i):
    return compute_value(f,i)*(f < freq_break(i+1))

  def compute_next(f,i):
    return compute_value(f,i)\
      *(f < freq_break(i+1))*(f >= freq_break(i))

  def compute_last(f,i):
    return compute_value(f,i)*(f >= freq_break(i))


  y = compute_first(f,0)
  for i in range(1,n-1):
    y += compute_next(f,i)

  y += compute_last(f,n-1)
  return y

def plot_posy(name,X,Y,model,n):
  YH = list(map(lambda x: predict_posy(model,max(X),x,n), X))
  plt.scatter(X,Y,label='data')
  plt.plot(X,YH,label='fit')
  plt.savefig(name)
  plt.clf()

def compute_posy(prefix,X,data,n=5,extern_breaks=None):
  init_conds = []
  params = []
  lb,ub= [],[]
  unk = (-np.inf,np.inf)
  params += ['bsc']
  lb += [1e-3]
  ub += [1.0]
  init_conds += [1.0]

  for i in range(0,n):
    params += ['x[%d]'%i,'y[%d]' % i,
               'v[%d]'%i,'u[%d]'%i,
               'w[%d]'%i]
    vmin = 1e-6
    vmax = 2
    cmax = 100.0
    # x, y and z
    lb += [vmin,vmin]
    ub += [cmax,cmax]
    # u, v and q
    lb += [vmin,vmin]
    ub += [vmax,vmax]
    # w
    lb += [0]
    ub += [np.inf]
    init_conds += [1.0,1.0]
    init_conds += [1.0,1.0]
    init_conds += [0.0]

  def posy_fit(f,*pvals):
    pdict = dict(zip(params,pvals))
    return predict_posy(pdict,max(f),f,n)


  pwls = {}
  for field in data.keys():
     print("==== %s ====" % field)
     Y = abs(np.array(data[field]))
     popt_pw, pcov = scipy.optimize.curve_fit(posy_fit,\
                                              X, Y,
                                              p0=init_conds,
                                              bounds=(lb,ub))

     model = dict(zip(params,popt_pw))
     plot_posy('%s_%s.png' % (prefix,field), X, Y, model, n)

     pwls[field] = {
       'x': list(map(lambda i: abs(model['x[%d]'%i]),range(0,n))),
       'y': list(map(lambda i: abs(model['y[%d]'%i]),range(0,n))),
       'u': list(map(lambda i: abs(model['u[%d]'%i]),range(0,n))),
       'v': list(map(lambda i: abs(model['v[%d]'%i]),range(0,n))),
       'w': list(map(lambda i: abs(model['w[%d]'%i]),range(0,n)))
     }

  breaks = breaks_posy(max(X),n)*model['bsc']
  breaks[0] = 0
  pwls['breaks'] = breaks


  return pwls
'''
def compute_pwls(basename,X,data,n=3,extern_breaks=None):

  all_breaks = []
  pwls = {}
  for field in data.keys():
    print("==== %s ====" % field)
    Y = data[field]
    do_fit = pwlf.PiecewiseLinFit(X,Y,sorted_data=True)
    if extern_breaks is None:
      breaks = do_fit.fit(n)
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
    plot_pwl('%s_%s.png' % (basename,field), X, Y, do_fit)

  
  return pwls

'''
