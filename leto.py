from lang.prog import MathProg
from ops import op
from compiler import arco, jaunt

def benchmark2():
    prob = MathProg()

    prob.bind("x1",op.Integ(op.Var("x2"), op.Const(0)))
    prob.bind("x0",op.Integ(op.Var("x1"), op.Const(-1)))

    term0 = op.Const(1.5*0.5)
    term1 = op.Mult(op.Const(0.6*0.5),op.Var("x1"))
    term2 = op.Mult(op.Var("x0"),op.Var("x0"))
    term3 = op.Var("x0")

    # compilation is performing transformations than compiling.
    prob.bind("x2",op.Mult(op.Const(0.5),
                        op.Add(term0,
                                op.Mult(op.Const(-1.0),
                                        op.Add(term1,op.Add(term2,term3))))))

    return prob

def benchmark_mm():
    prob = MathProg()
    kf = 1e-4
    kr = 1e-2
    E0 = 4400
    S0 = 6600
    ES = op.Integ(op.Add(
        op.Mult(op.Const(kf),
                op.Mult(op.Var("S"),op.Var("E"))),
        op.Mult(op.Const(-1*kr),op.Var("ES"))), op.Const(0))

    E = op.Add(op.Const(E0),
               op.Mult(op.Var("ES"), op.Const(-1)))

    S = op.Add(op.Const(S0),
               op.Mult(op.Var("ES"), op.Const(-1)))

    prob.bind("E",E)
    prob.bind("S",S)
    prob.bind("ES",ES)
    #prob.bind("_y", op.Emit(op.Var("y")))
    return prob


def benchmark1():
    prob = MathProg()
    dy2 = op.Add(
        op.Mult(op.Var("dy1"),op.Const(-0.2)),
        op.Mult(op.Var("y"),op.Const(-0.8))
    )
    dy1 = op.Integ(op.Var("dy2"), op.Const(-2))
    y = op.Integ(op.Var("dy1"), op.Const(9))

    prob.bind("dy2",dy2)
    prob.bind("dy1",dy1)
    prob.bind("y",y)
    #prob.bind("_y", op.Emit(op.Var("y")))
    return prob


def benchmark0():
    prob = MathProg()
    prob.bind("x", op.ExtInput(op.Var("_x",constant=True)))
    prob.bind("y", op.Mult(op.Var("x"), op.Const(2.0)))
    #prob.bind("_y", op.Emit(op.Var("y")))

#import conc
from chip.hcdc import board as hdacv2_board
#import srcgen
#import jaunt
#import conc_bmarks
#from spec import board as hdacv2_board
#import superoptimizer as superopt
# the math problem in the example
prob = benchmark1()
for abs_circ in arco.compile(hdacv2_board,prob):

    raw_input()
    for idx,out_circ in enumerate(jaunt.scale(conc_circ)):
        print(out_circ)

#circ_name,exp_name,out_name = "damped_spring","simulate","test1"
#circ_name,exp_name,out_name = "double_with_mult","param_sweep","test2"
#circ_name,exp_name,out_name = "double_with_plus","param_sweep","test4"
#circ_name,exp_name,out_name = "in_to_out","param_sweep","test3"
#orig_circ = conc_bmarks.get(circ_name)
#experiment = conc_bmarks.experiment(circ_name,exp_name)
files = []
for idx,circ in enumerate(jaunt.scale(orig_circ)):
    srcgen.Logger.DEBUG = True
    srcgen.Logger.NATIVE = True
    circ.name = "%s_%d" % (circ_name,idx)
    labels,circ_cpp, circ_h = srcgen.generate(circ)
    files.append((labels,circ.name,circ_cpp,circ_h))


print(len(files))
srcgen.write_file(experiment,files,out_name,circs=[orig_circ])
