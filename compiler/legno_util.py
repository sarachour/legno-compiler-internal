from util import paths
#from compiler import lgraph, lscale, srcgen, execprog
import os
import time
import json
import shutil
import numpy as np
from util.util import Timer
import itertools
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
    timer = Timer('lgraph_%s' % args.program,path_handler)
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
        filename = path_handler.abs_circ_file(indices)
        adp.write_circuit(filename)

        print("<<< writing graph >>>")
        filename = path_handler.abs_graph_file(indices)
        adp.write_graph(filename,write_png=True)

        count += 1
        if count >= args.max_circuits:
            break

        timer.start()

    print("<<< done >>>")
    timer.kill()
    print(timer)
    timer.save()

def exec_lscale_normal(prog,conc_circ,args):
    for idx,opt,model,scale_circ in lscale.scale(prog, \
                                                 conc_circ,
                                                 args.scale_circuits,
                                                 model=args.model,
                                                 max_freq=args.max_freq,
                                                 digital_error=args.digital_error,
                                                 analog_error=args.analog_error,
                                                 do_log=True):
        yield idx,opt,model,scale_circ


def exec_lscale_search(prog,conc_circ,args,tolerance=0.002):
    def test_valid(digital_error,analog_error):
        print("dig_error=%f an_error=%f" % (digital_error,analog_error))
        for idx,opt,model,scale_circ in lscale.scale(prog, \
                                                    conc_circ,
                                                    args.scale_circuits,
                                                    model=args.model,
                                                    max_freq=args.max_freq,
                                                    digital_error=digital_error,
                                                    analog_error=analog_error,
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

            is_valid = test_valid(max_value,error) if analog \
                       else test_valid(error,max_value)
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

    for scale in [1.1]:
        for idx,opt,model,scale_circ in lscale.scale(prog, \
                                                    conc_circ,
                                                    args.scale_circuits,
                                                    model=args.model,
                                                    max_freq=args.max_freq,
                                                    digital_error=dig_error*scale,
                                                    analog_error=analog_error*scale):
            yield idx,opt,model,scale_circ



def exec_lscale(args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  prog = bmark.get_prog(args.benchmark)
  circ_dir = path_handler.abs_circ_dir()
  timer = Timer('lscale_%s' % args.benchmark, path_handler)
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        circ_bmark,circ_indices = path_handler \
                                  .abs_circ_to_args(fname)
        print('<<<< %s >>>>' % fname)
        filename = "%s/%s" % (dirname,fname)
        conc_circ = ConcCirc.read(hdacv2_board, filename)

        timer.start()
        gen = exec_lscale_normal(prog,conc_circ,args) if not args.search \
              else exec_lscale_search(prog,conc_circ,args)

        for idx,opt,model,scale_circ in gen:
            filename = path_handler.conc_circ_file(circ_bmark,
                                                   circ_indices,
                                                   idx,
                                                   model,
                                                   opt)
            timer.end()
            scale_circ.write_circuit(filename)
            filename = path_handler.conc_graph_file(circ_bmark,
                                                    circ_indices,
                                                    idx,
                                                    model,
                                                    opt)
            scale_circ.write_graph(filename,write_png=True)
            timer.start()
        timer.kill()

    print(timer)
    timer.save()

def exec_srcgen(hdacv2_board,args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  menv = bmark.get_math_env(args.benchmark)
  hwenv = hwenvs.get_hw_env(args.hw_env)
  recompute = args.recompute
  circ_dir = path_handler.conc_circ_dir()
  timer = Timer('srcgen_%s' % args.benchmark,path_handler)
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        print('<<<< %s >>>>' % fname)
        circ_bmark,circ_indices,circ_scale_index,circ_method,circ_opt = \
            path_handler.conc_circ_to_args(fname)
        filename = path_handler.grendel_file(circ_bmark, \
                                             circ_indices, \
                                             circ_scale_index, \
                                             circ_method, \
                                             circ_opt,
                                             menv.name,
                                             hwenv.name)

        if path_handler.has_file(filename) and not recompute:
            continue

        conc_circ = ConcCirc.read(hdacv2_board,"%s/%s" % (dirname,fname))
        timer.start()
        gren_file = srcgen.generate(path_handler,
                                    hdacv2_board,\
                                    conc_circ,\
                                    menv,
                                    hwenv,
                                    filename=filename,
                                    ntrials=args.trials)
        timer.end()
        gren_file.write(filename)

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
