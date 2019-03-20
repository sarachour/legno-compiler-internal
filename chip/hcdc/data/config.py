data={
  'block': {
    'baseline':2.0,
    'coeffs': {
      'integ':0.005,
      'mult':1.0,
      'vga':0.5,
      'dac':0.01,
      'adc':0.01,
      'fanout':0.005
    }
  },
  'scale-mode': {
    'delta':0.0
  },
  'coeff-mode': {
    'delta':0.0
  },
  'signal': {
    'weights':{
      'mult':0.0
    }
  },
  'freq': {
    'exponent':1.0,
    'coeffs': {
      'integ':0.3
    }
  },
}

spec={
  'block': {
    'baseline':[0.1,5.0],
    'coeffs': {
      'integ':[0,1],
      'mult':[0,1],
      'vga':[0,1],
      'dac':[0,1],
      'adc':[0,1],
      'fanout':[0,1]
    }
  },
  'scale-mode': {
    'delta':[0,0.2]
  },
  'coeff-mode': {
    'delta':[0,0.2]
  },
  'signal': {
    'weights':{
      'mult':[0,0.05]
    }
  },
  'freq': {
    'exponent':[0.5,2.0],
    'coeffs': {
      'integ':[0.1,5.0]
    }
  }
}
