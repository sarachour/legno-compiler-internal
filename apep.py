## generate tests for noise modelling
from chip.hcdc import board
import chip.conc as ccirc
from chip.block import Labels
import lang.experiment as experiments
import gen.srcgen as srcgen
import os

def boilerplate(name,loc,chip_adc=False,chip_dac=False):
    circ = ccirc.ConcCirc(board,name)
    board_name,chip_no,slice_no,tile_no,idx = loc
    circ.set_tau(1.0)
    in_ret = None
    out_ret = None
    if chip_adc:
        out_loc = [board_name,chip_no,3,2]
        circ.use("due_adc",out_loc)
        circ.config("due_adc",out_loc)\
            .set_label("out","OUT",scf=1.0,kind=Labels.OUTPUT)
        out_ret = ("due_adc",out_loc,"in")

    if chip_dac:
        in_loc = [board_name,chip_no,3,2]
        addr = circ.use("due_dac",[board_name,chip_no,3,2])
        circ.config(addr).set_label("in","X",scf=1.0,kind=Labels.DYNAMIC_INPUT)
        out_ret = ("due_dac",in_loc,"out")

    return circ,in_ret,out_ret

def route(circ,sblk,sloc,sport,dblk,dloc,dport):
    for route in circ.find_routes(sblk,sloc,sport,dblk,dloc,dport):
        for idx in range(0,len(route),2):
            srcblk,srcloc,srcport = route[idx]
            dstblk,dstloc,dstport= route[idx+1]
            circ.use(srcblk,srcloc)
            circ.use(dstblk,dstloc)
            circ.conn(srcblk,srcloc,srcport,dstblk,dstloc,dstport)

        return True

    print("impossible: <%s%s.%s> to <%s%s.%s>" % \
                    (sblk,sloc,sport,dblk,dloc,dport))
    return False

# generate dac
def gen_dac(loc):
    locstr = "_".join(map(lambda x : str(x), loc))
    circ,ana_in,ana_out= boilerplate("calib_dac_%s" % locstr,
                                 loc,
                                 chip_adc=True,
                                 chip_dac=False)

    assert(ana_in is None)
    assert(not ana_out is None)
    ana_out_block,ana_out_loc,ana_out_port = ana_out
    addr = circ.use("tile_dac",loc)
    exp = experiments.ParameterSweepExperiment(2400,100)
    exp.sweep("INP",-1.0,1.0)
    circ.config("tile_dac",loc) \
        .set_label("in","INP",scf=1.0,kind=Labels.CONST_INPUT) \
        .set_dac("in",0) \
        .set_scale_mode("pos")

    succ = route(circ,"tile_dac",loc,"out", \
                 ana_out_block,ana_out_loc,ana_out_port)
    if succ:
        return exp,circ
    else:
        return None

def gen_adc(loc):
    raise NotImplementedError

def gen_gain(loc):
    raise NotImplementedError

def gen_mult(loc):
    raise NotImplementedError

def gen_lut(loc):
    raise NotImplementedError

def gen_fanout(loc):
    raise NotImplementedError

def generate(dacs_only=False):
    for loc in board.instances_of_block('tile_dac'):
        locstr = "_".join(map(lambda x : str(x),loc))
        name = "calib_dac_%s" % locstr
        result = gen_dac(loc)
        if not result is None:
            yield name,result

    if dacs_only:
        return 

    for loc in board.instances_of_block('multiplier'):
        yield gen_mult(loc)
        yield gen_gain(loc)

    for loc in board.instances_of_block('fanout'):
        yield gen_fanout(loc)


    for loc in board.instances_of_block('lut'):
        yield gen_lut(loc)


    for loc in board.instances_of_block('integ'):
        yield gen_integ(loc)


calib_dir = "transform"
if not os.path.exists(calib_dir):
    os.mkdir(calib_dir)

for file_name,(experiment,circ) in generate(dacs_only=True):
    labels,circ_cpp, circ_h = srcgen.generate(circ,recover=False)
    srcgen.write_file(experiment,
                      [(labels,circ.name,circ_cpp,circ_h)],
                      file_name,
                      parent_dir=calib_dir,
                      circs=[circ])


calib_dir = "calibrate"
if not os.path.exists(calib_dir):
    os.mkdir(calib_dir)


for file_name,(experiment,circ) in generate():
    labels,circ_cpp, circ_h = srcgen.generate(circ)
    srcgen.write_file(experiment,
                      [(labels,circ.name,circ_cpp,circ_h)],
                      file_name,
                      parent_dir=calib_dir,
                      circs=[circ])

