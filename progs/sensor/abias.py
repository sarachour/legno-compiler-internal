'''
def ext(t):
    x =  math.sin(t)*math.cos(t)
    if t > 20 and t < 28:
        return abs(x)
    return x
def state_machine(z,t):
    u = ext(t)
    x,s = z
    dx = 0.4*u - 0.1*x
    ds = 0.1*x - 0.05*s
    return [dx,ds]

'''
