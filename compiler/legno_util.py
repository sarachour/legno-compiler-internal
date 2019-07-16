import bmark.hwenvs as hwenvs
import bmark.diffeqs as bmark
from util import paths
from compiler import arco, jaunt, srcgen, execprog, skelter
from chip.conc import ConcCirc
import os
import time
import json
import shutil
import numpy as np
from util.util import Timer
import itertools

# TODO: in concrete specification, connection is made to same dest.
def compile(board,problem):
    files = []
    prob = benchmark1()
    for idx1,idx2,circ in compile(hdacv2_board,prob):
        srcgen.Logger.DEBUG = True
        srcgen.Logger.NATIVE = True
        circ.name = "%s_%d_%d" % (circ_name,idx1,idx2)
        labels,circ_cpp, circ_h = srcgen.generate(circ)
        files = []
        files.append((labels,circ.name,circ_cpp,circ_h))
        srcgen.write_file(experiment,files,out_name,
                        circs=[circ])

def exec_ref(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  prog = bmark.get_prog(args.benchmark)
  menv = bmark.get_math_env(args.benchmark)
  execprog.execute(path_handler,
                   prog,
                   menv)

def exec_arco(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  problem = bmark.get_prog(args.benchmark)

  timer = Timer('arco_%s' % args.benchmark,path_handler)
  timer.start()
  for indices,conc_circ in \
      arco.compile(hdacv2_board,
                              problem,
                              depth=args.xforms,
                              max_abs_circs=args.abs_circuits,
                              max_conc_circs=args.conc_circuits):

      timer.end()
      filename = path_handler.abs_circ_file(indices)
      print("<<< writing circuit>>>")
      conc_circ.write_circuit(filename)
      filename = path_handler.abs_graph_file(indices)
      print("<<< writing graph >>>")
      conc_circ.write_graph(filename,write_png=True)
      timer.start()

  timer.kill()
  print(timer)
  timer.save()

def exec_jaunt_normal(prog,conc_circ,args):
    for idx,opt,model,scale_circ in jaunt.scale(prog, \
                                                conc_circ,
                                                args.scale_circuits,
                                                model=args.model,
                                                digital_error=args.digital_error,
                                                analog_error=args.analog_error):
        yield idx,opt,model,scale_circ


def exec_jaunt_search(prog,conc_circ,args,tolerance=0.002):
    def test_valid(digital_error,analog_error):
        print("dig_error=%f an_error=%f" % (digital_error,analog_error))
        for idx,opt,model,scale_circ in jaunt.scale(prog, \
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
        for idx,opt,model,scale_circ in jaunt.scale(prog, \
                                                    conc_circ,
                                                    args.scale_circuits,
                                                    model=args.model,
                                                    max_freq=args.max_freq,
                                                    digital_error=dig_error*scale,
                                                    analog_error=analog_error*scale):
            yield idx,opt,model,scale_circ



def exec_jaunt(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  prog = bmark.get_prog(args.benchmark)
  circ_dir = path_handler.abs_circ_dir()
  timer = Timer('jaunt_%s' % args.benchmark, path_handler)
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        circ_bmark,circ_indices = path_handler \
                                  .abs_circ_to_args(fname)
        print('<<<< %s >>>>' % fname)
        filename = "%s/%s" % (dirname,fname)
        conc_circ = ConcCirc.read(hdacv2_board, filename)

        timer.start()
        gen = exec_jaunt_normal(prog,conc_circ,args) if not args.search \
              else exec_jaunt_search(prog,conc_circ,args)

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

def exec_graph(hdacv2_board, args):
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
