import conc
from hcdc import board as hdacv2_board
import experiments

def in_to_out():
    circ = conc.ConcCirc(hdacv2_board,"in_to_out")
    dac_X = circ.use("tile_dac", [0,0,0,0])
    tileout = circ.use("tile_out", [0,0,0,0])
    chipout = circ.use("due_adc", [0,3,2])

    circ.conn(dac_X,"out",tileout,"in")
    circ.conn(tileout,"out",chipout,"in")

    circ.config(dac_X) \
        .set_label("in","x",kind=conc.Labels.CONST_INPUT)

    circ.config(chipout) \
        .set_label("out","y",kind=conc.Labels.OUTPUT)

    circ.set_interval("x",-1.0,1.0)
    circ.set_interval("y",-1.0,1.0)
    return circ


def double_with_times():
    circ = conc.ConcCirc(hdacv2_board,"double_with_times")
    dac_X = circ.use("tile_dac", [0,0,0,0])
    mul_X = circ.use("multiplier", [0,0,0,0])
    tileout = circ.use("tile_out", [0,0,0,0])
    chipout = circ.use("due_adc", [0,3,2])

    circ.conn(dac_X,"out",mul_X,"in0")
    circ.conn(mul_X,"out",tileout,"in")
    circ.conn(tileout,"out",chipout,"in")

    circ.config(mul_X).set_dac("coeff",2.0) \
                      .set_mode("vga") \
                      .set_scale_mode("med")

    circ.config(dac_X) \
        .set_label("in","x",kind=conc.Labels.CONST_INPUT)

    circ.config(chipout) \
        .set_label("out","y",kind=conc.Labels.OUTPUT)

    circ.set_interval("x",-2.0,2.0)
    circ.set_interval("y",-4.0,4.0)
    return circ

def double_with_plus():
    circ = conc.ConcCirc(hdacv2_board,"double_with_plus")
    dac_X = circ.use("tile_dac", [0,0,0,0])
    fan_X = circ.use("fanout", [0,0,0,0])
    tileout = circ.use("tile_out", [0,0,0,0])
    chipout = circ.use("due_adc", [0,3,2])


    circ.conn(dac_X,"out",fan_X,"in")
    circ.conn(fan_X,"out0",tileout,"in")
    circ.conn(fan_X,"out1",tileout,"in")
    circ.conn(tileout,"out",chipout,"in")

    circ.config(dac_X) \
        .set_label("in","x",kind=conc.Labels.CONST_INPUT)

    circ.config(chipout) \
        .set_label("out","y",kind=conc.Labels.OUTPUT)

    circ.set_interval("x",-2.0,2.0)
    circ.set_interval("y",-4.0,4.0)


    return circ

def michaelis_menten():
    circ = conc.ConcCirc(hdacv2_board,"michaelis_menten")

    ic_E = 200
    ic_S = 400
    ic_ES = 100
    kf = 0.003
    kr = 0.004

    dac_E0 = circ.use("tile_dac", [0,0,0,0])
    dac_S0 = circ.use("tile_dac", [0,0,1,0])
    fan_E = circ.use("fanout", [0,0,0,1])
    fan_S = circ.use("fanout", [0,0,0,0])

    circ.config(dac_E0).set_dac("in",ic_E)
    circ.config(dac_S0).set_dac("in",ic_S)
    circ.conn(dac_E0,"out",dac_E)
    circ.conn(dac_S0,"out",dac_S)

    mul_E_S = circ.use("multiplier", [0,0,0,0])
    mul_kf_E_S = circ.use("multiplier", [0,0,0,1])

    circ.config(mul_kf_E_S).set_mode("vga") \
                    .set_scale_mode(["med","pos"])\
                    .set_dac("coeff",kf)


    # kf*E*S
    circ.conn(fan_S,"out0",mul_E_S,"in0")
    circ.conn(fan_E,"out1",mul_E_S,"in1")
    circ.conn(mul_E_S,"out",mul_kf_E_S,"in0")

    fan_ES = circ.use("fanout", [0,0,1,0])
    fan_ES2 = circ.use("fanout", [0,0,1,1])
    int_ES = circ.use("integrator", [0,0,1,0])
    mul_kr_ES = circ.use("multiplier", [0,0,1,0])

    circ.config(int_ES).set_dac("ic", ic_ES)
    # -kr*ES
    circ.config(mul_kr_ES).set_mode("vga") \
                    .set_scale_mode(["med","neg"])\
                    .set_dac("coeff",kr)

    # invert two signals
    circ.config(fan_ES).set_scale_mode(["pos","neg","neg"])

    circ.conn(fan_ES,"out0",fan_ES2,"in")
    circ.conn(fan_ES,"out1",fan_E,"in")
    circ.conn(fan_ES,"out2",fan_S,"in")

    circ.conn(fan_ES2,"out0",mul_kr_ES,"in0")

    circ.conn(mul_kr_ES,"out",int_ES,"in")
    circ.conn(mul_kf_E_S,"out",int_ES,"in")

    circ.set_interval("E",0,300)
    circ.set_interval("S",0,500)
    circ.set_interval("ES",0,300)

    return circ


def damped_spring():

    circ = conc.ConcCirc(hdacv2_board,"damped_spring")

    # chip, tile, slice, block_idx
    int0 = circ.use("integrator", [0,0,0,0])
    int1 = circ.use("integrator", [0,1,0,0])

    fan0 = circ.use("fanout", [0,0,0,1])
    fan1 = circ.use("fanout", [0,1,0,1])

    mul0 = circ.use("multiplier", [0,0,0,1])
    mul1 = circ.use("multiplier", [0,1,0,1])

    tileout = circ.use("tile_out", [0,1,0,1])
    out0 = circ.use("tile_out", [0,0,0,0])
    in0 = circ.use("tile_in", [0,0,0,0])
    out1 = circ.use("tile_out", [0,1,0,0])
    in1 = circ.use("tile_in", [0,1,0,0])

    for blk in [tileout,out0,in0,out1,in1]:
        circ.config(blk).set_mode("default")

    # 10x speed
    TC = 126*1000.0
    PI = 3.14159
    TAU = 2*PI*(20*1000)/TC
    SCF = 5.0

    print("TAU=%s" % TAU)
    print("SCF=%s" % SCF)

    # mass spring damper with only viscous friction
    eqn = "y'' = -0.2y' - 0.8y"
    ics = "y(0) = 9; y(0)' = -2"
    # 1/8x = 0.125x
    time = "60 s" # 478 us
    solution = "y=0"

    coeff1 = -0.2
    coeff2 = -0.8
    ic_y0 = 9
    ic_y1 = -2

    #coeff_value1 = 102
    #coeff_value2 = 0
    #coeff_value3 = 26
    coeff1 = 102
    coeff2 = 26
    ic_y1 = 102
    ic_y0 = 0

    # TODO: fix value
    # y'(0)
    #circ.config(int0).set_dac("ic", coeff_value1)
    circ.set_interval("pos",-10,10)
    circ.set_interval("vel",-5,5)

    circ.config(int0).set_dac("ic", ic_y1)\
                    .set_scale_mode(["med","med","pos"]) \
                    .set_label("out","vel")

    circ.config(fan0).set_scale_mode(["pos"]*3)
    circ.conn(int0,"out",fan0,"in")


    circ.config(int1).set_dac("ic", ic_y0) \
                    .set_scale_mode(["med","med","pos"]) \
                    .set_label("out","pos")

    circ.config(fan1).set_scale_mode(["pos"]*3)
    circ.conn(int1,"out",fan1,"in")

    circ.conn(fan0,"out0", out0,"in")
    circ.conn(out0,"out", in1,"in")
    circ.conn(in1,"out", int1,"in")

    circ.conn(fan1,"out0", tileout, "in")

    # TODO: fix value
    # coeff1 = 0.2
    #circ.config(mul0).set_mode("vga").set_dac("coeff",coeff_value1)
    circ.config(mul0).set_mode("vga") \
                    .set_scale_mode("med")\
                    .set_dac("coeff",coeff1)

    circ.conn(fan0, "out1", mul0, "in0")
    circ.conn(mul0, "out", int0, "in")


    # coeff2 = 0.8
    #circ.config(mul1).set_mode("vga").set_dac("coeff",coeff_value3)
    circ.config(mul1).set_mode("vga") \
                    .set_scale_mode("med") \
                    .set_dac("coeff",coeff2)

    circ.conn(fan1,"out1",mul1,"in0")
    circ.conn(mul1,"out",out1,"in")
    circ.conn(out1,"out",in0,"in")
    circ.conn(in0,"out",int0,"in")

    chipout = circ.use("due_adc", [0,3,2])
    circ.config(chipout) \
        .set_label("out","pos") \
        .set_mode("default")

    circ.conn(tileout,"out", chipout, "in")

    circ.check()

    return circ

def experiment(name,expname):
    if name == "double_with_plus"  \
       or name == "double_with_mult":
        if expname == "param_sweep":
            exp = experiments. \
                  ParameterSweepExperiment(100,npts=10)
            exp.sweep("x",-2,2)
            return exp


    elif name == "in_to_out":
        if expname == "param_sweep":
            exp = experiments. \
                  ParameterSweepExperiment(100,npts=10)
            exp.sweep("x",-1,1)
            return exp

    elif name == "damped_spring":
        if expname == "simulate":
            exp = experiments.TimeSeriesExperiment(300)
            return exp

    raise Exception("unrecognized experiment <%s>.<%s>" % \
                    (name,expname))

def get(name):
    if name == "damped_spring":
        return damped_spring()

    elif name == "double_with_plus":
        return double_with_plus()

    elif name == "double_with_mult":
        return double_with_times()

    elif name == "michaelis_menten":
        return michaelis_menten()

    elif name == "in_to_out":
        return in_to_out()
    else:
        raise Exception("unknown benchmark <%s>" % name)
