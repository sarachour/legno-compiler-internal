
## whitebox models
# each model has a whitebox and a blackbox description.
# first thing we do is alignment

def due_dac(inp):
  assert(inp <= 1.0 and inp >= -1.0)
  return 1.1*(inp+1.0) + 0.55

def vdiv(inp):
  assert(inp >= 0.55 and inp <= 0.275)
  return 0.027272727*inp - 0.045

# vtoi0: -5 mv
# vtoi1: 5 mv
def vtoi(inp):
  assert(inp >= -0.030 and inpt <= 0.030)
  3.63e-5*(inp-0.0096)

def itov(inp):
  assert(inp <= 2e-6 and inp >= -2e-6)
  6.0e5*inp

def mult(inp0,inp1):
  return inp0*inp1
