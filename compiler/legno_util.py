#from compiler import lgraph, lscale, srcgen, execprog
import os
import time
import json
import shutil
import numpy as np
import itertools
import util.util as util
import util.paths as paths
from hwlib.adp import AnalogDeviceProg
from dslang.dsprog import DSProgDB

def exec_lgraph(args):
    from compiler import lgraph
    from hwlib.hcdc.hcdcv2_4 import make_board
    from hwlib.hcdc.globals import HCDCSubset

    hdacv2_board = make_board(HCDCSubset(args.subset), \
                              load_conns=True)
    path_handler = paths.PathHandler(args.subset,args.program)
    program = DSProgDB.get_prog(args.program)
    timer = util.Timer('lgraph',path_handler)
    timer.start()
    count = 0
    for indices,adp in \
        lgraph.compile(hdacv2_board,
                       program,
                       depth=args.xforms,
                       max_abs_circs=args.abs_circuits,
                       max_conc_circs=args.conc_circuits):
        timer.end()

        print("<<< writing circuit>>>")
        filename = path_handler.lgraph_adp_file(indices)
        adp.write_circuit(filename)

        print("<<< writing graph >>>")
        filename = path_handler.lgraph_adp_diagram_file(indices)
        adp.write_graph(filename,write_png=True)

        count += 1
        if count >= args.max_circuits:
            break

        timer.start()

    print("<<< done >>>")
    timer.kill()
    print(timer)
    timer.save()

def exec_lscale_normal(timer,prog,adp,args):
    from compiler import lscale
    timer.start()
    for idx,opt,model,scale_circ in lscale.scale(prog, \
                                                 adp,
                                                 args.scale_circuits,
                                                 model=util.DeltaModel(args.model),
                                                 max_freq_khz=args.max_freq,
                                                 mdpe=args.mdpe/100.0,
                                                 mape=args.mape/100.0,
                                                 do_log=True):
        timer.end()
        yield idx,opt,model,scale_circ


def exec_lscale_search(timer,prog,adp,args,tolerance=0.002):
    from compiler import lscale
    def test_valid(mdpe,mape):
        print("mdpe=%f mape=%f" % (mdpe,mape))
        for idx,opt,model,scale_circ in lscale.scale(prog, \
                                                    adp,
                                                    args.scale_circuits,
                                                    model=util.DeltaModel(args.model),
                                                    max_freq_khz=args.max_freq,
                                                    mdpe=mdpe,
                                                    mape=mape,
                                                    do_log=True):
            return True
        return False



    def recursive_grid_search(rng,analog=True,n=2,max_value=1.0,failures=[]):
        vals = np.linspace(rng[0], \
                               rng[1], n)
        if abs(rng[0]-rng[1]) < tolerance:
            return None

        succs,fails = [],[]
        for error in vals:
            if error in failures:
                fails.append(error)
                continue;

            is_valid = test_valid(mdpe=max_value,mape=error) if analog \
                       else test_valid(mdpe=error,mape=max_value)
            if is_valid:
                succs.append(error)
                break;
            else:
                fails.append(error)


        if len(succs) > 0:
            best = min(succs)
            worst = max(fails) if len(fails) > 0 else rng[0]
            if best < rng[1] or worst > rng[0]:
                best = recursive_grid_search( \
                                              [worst,best], \
                                              analog=analog, \
                                              max_value=max_value, \
                                              n=n,
                                              failures=failures+fails)
                best = min(succs) if best is None else best
            return best
        else:
            return None


    def joint_search(dig_error,alog_error):
        if test_valid(dig_error,alog_error):
            return dig_error,alog_error

        dig,alog = joint_search(dig_error+tolerance,alog_error+tolerance)
        return dig,alog

    max_pct = 1.0
    succ = test_valid(max_pct,max_pct)
    while not succ and max_pct <= 1e6:
        max_pct *= 2
        succ = test_valid(max_pct,max_pct)

    if max_pct >= 1e6:
        return

    dig_error= recursive_grid_search([0.01,max_pct], \
                                     max_value=max_pct,
                                     analog=False,n=3)
    analog_error= recursive_grid_search([0.01,max_pct], \
                                        max_value=max_pct, \
                                        analog=True,n=3)

    dig_error,analog_error = joint_search(dig_error,analog_error)

    timer.kill()
    for scale in [1.1]:
        timer.start()
        for idx,opt,model,scale_circ in lscale.scale(prog, \
                                                     adp,
                                                     args.scale_circuits,
                                                     model=util.DeltaModel(args.model),
                                                     max_freq_khz=args.max_freq,
                                                     mdpe=dig_error*scale,
                                                     mape=analog_error*scale):
            timer.end()
            timer.start()
            yield idx,opt,model,scale_circ



def exec_lscale(args):
    from hwlib.hcdc.hcdcv2_4 import make_board
    from hwlib.hcdc.globals import HCDCSubset

    hdacv2_board = make_board(HCDCSubset(args.subset), \
                              load_conns=False)
    path_handler = paths.PathHandler(args.subset,args.program)
    program = DSProgDB.get_prog(args.program)
    timer = util.Timer('lscale',path_handler)
    adp_dir = path_handler.lgraph_adp_dir()
    for dirname, subdirlist, filelist in os.walk(adp_dir):
        for lgraph_adp_file in filelist:
            if lgraph_adp_file.endswith('.adp'):
                fileargs = path_handler \
                           .lgraph_adp_to_args(lgraph_adp_file)
                print('<<<< %s >>>>' % lgraph_adp_file)
                lgraph_adp_filepath = "%s/%s" % (dirname,lgraph_adp_file)
                adp = AnalogDeviceProg.read(hdacv2_board, \
                                            lgraph_adp_filepath)

                gen = exec_lscale_normal(timer,program,adp,args) if not args.search \
                      else exec_lscale_search(timer,program,adp,args)

                for scale_index,opt,model,scale_adp in gen:
                    lscale_adp_file = path_handler.lscale_adp_file(fileargs['lgraph'],
                                                            scale_index,
                                                            model,
                                                            opt)
                    scale_adp.write_circuit(lscale_adp_file)
                    lscale_diag_file = path_handler.lscale_adp_diagram_file(fileargs['lgraph'],
                                                                    scale_index,
                                                                    model,
                                                                    opt)
                    scale_adp.write_graph(lscale_diag_file,write_png=True)

    timer.kill()
    timer.save()

def exec_srcgen(args):
    from compiler import srcgen
    import hwlib.hcdc.hwenvs as hwenvs
    from hwlib.hcdc.hcdcv2_4 import make_board
    from hwlib.hcdc.globals import HCDCSubset

    hdacv2_board = make_board(HCDCSubset(args.subset), \
                              load_conns=False)
    path_handler = paths.PathHandler(args.subset,args.program)
    dssim = DSProgDB.get_sim(args.program)
    hwenv = hwenvs.get_hw_env(args.hw_env)
    adp_dir = path_handler.lscale_adp_dir()
    timer = util.Timer('srcgen', path_handler)
    for dirname, subdirlist, filelist in os.walk(adp_dir):
        for adp_file in filelist:
            if adp_file.endswith('.adp'):
                print('<<<< %s >>>>' % adp_file)
                fileargs  = \
                            path_handler.lscale_adp_to_args(adp_file)
                gren_file = path_handler.grendel_file(fileargs['lgraph'], \
                                                     fileargs['lscale'], \
                                                     fileargs['model'], \
                                                     fileargs['opt'],
                                                     dssim.name,
                                                     hwenv.name)

                if path_handler.has_file(gren_file) and not args.recompute:
                    continue

                adp_filepath = "%s/%s" % (dirname,adp_file)
                conc_circ = AnalogDeviceProg.read(hdacv2_board,adp_filepath)
                timer.start()
                gren_prog = srcgen.generate(path_handler,
                                            hdacv2_board,\
                                            conc_circ,\
                                            dssim,
                                            hwenv,
                                            filename=gren_file,
                                            ntrials=args.trials)
                timer.end()
                gren_prog.write(gren_file)

    print(timer)
    timer.save()



def exec_graph_one(hdacv2_board,path_handler,fname):
    dirname = path_handler.conc_circ_dir()
    circ_bmark,circ_indices,circ_scale_index,model,opt = \
                                                   path_handler \
                                                   .conc_circ_to_args(fname)

    conc_circ = path_handler.conc_circ_file(circ_bmark,
                                            circ_indices,
                                            circ_scale_index,
                                            model,
                                            opt)
    print('<<<< %s >>>>' % fname)
    with open("%s/%s" % (dirname,fname),'r') as fh:
        obj = json.loads(fh.read())
        conc_circ = ConcCirc.from_json(hdacv2_board, \
                                       obj)

        path_handler.extract_metadata_from_filename(conc_circ, fname)
        methods = ['snr','pctrng']
        for draw_method in methods:
            filename = path_handler.conc_graph_file(circ_bmark,
                                                    circ_indices,
                                                    circ_scale_index,
                                                    model,
                                                    opt,
                                                    tag=draw_method)
            conc_circ.write_graph(filename,\
                                  write_png=True,\
                                  color_method=draw_method)

def exec_visualize(args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  circ_dir = path_handler.conc_circ_dir()
  scores = []
  filenames = []
  if not args.circ is None:
      exec_graph_one(hdacv2_board,path_handler,args.circ)
      return

  for dirname, subdirlist, filelist in os.walk(circ_dir):
      print(dirname)
      for fname in filelist:
          print(fname)
          if fname.endswith('.circ'):
              print(fname)
              exec_graph_one(hdacv2_board,path_handler,fname)
