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

  for indices,conc_circ in \
      arco.compile(hdacv2_board,
                              problem,
                              depth=args.xforms,
                              max_abs_circs=args.abs_circuits,
                              max_conc_circs=args.conc_circuits):

      filename = path_handler.abs_circ_file(indices)
      print("<<< writing circuit>>>")
      conc_circ.write_circuit(filename)
      filename = path_handler.abs_graph_file(indices)
      print("<<< writing graph >>>")
      conc_circ.write_graph(filename,write_png=True)
      time.sleep(1)

def exec_jaunt_phys(hdacv2_board,args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  prog = bmark.get_prog(args.benchmark)
  circ_dir = path_handler.skelt_circ_dir()
  generated = {}
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        circ_bmark,circ_indices,circ_scale_index,circ_opt = \
           path_handler.conc_circ_to_args(fname)

        gen_key = (circ_bmark,str(circ_indices),circ_scale_index)
        if circ_opt in jaunt.JauntObjectiveFunctionManager.physical_methods():
          continue

        if gen_key in generated:
            continue

        filename = "%s/%s" % (dirname,fname)
        conc_circ = ConcCirc.read(hdacv2_board, filename)
        for opt,scaled_circ in jaunt.physical_scale(prog,conc_circ):
            filename = path_handler.conc_circ_file(circ_bmark,
                                                    circ_indices,
                                                    circ_scale_index,
                                                    opt)
            scaled_circ.write_circuit(filename)
            filename = path_handler.conc_graph_file(circ_bmark,
                                                    circ_indices,
                                                    circ_scale_index,
                                                    opt)
            scaled_circ.write_graph(filename,write_png=True)
            generated[gen_key] = True


def exec_jaunt(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  prog = bmark.get_prog(args.benchmark)
  circ_dir = path_handler.abs_circ_dir()
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        circ_bmark,circ_indices = path_handler \
                                  .abs_circ_to_args(fname)
        print('<<<< %s >>>>' % fname)
        filename = "%s/%s" % (dirname,fname)
        conc_circ = ConcCirc.read(hdacv2_board, filename)

        for idx,opt,scale_circ in jaunt.scale(prog,conc_circ):
            filename = path_handler.conc_circ_file(circ_bmark,
                                                    circ_indices,
                                                    idx,
                                                    opt)
            scale_circ.write_circuit(filename)
            filename = path_handler.conc_graph_file(circ_bmark,
                                                    circ_indices,
                                                    idx,
                                                    opt)
            scale_circ.write_graph(filename,write_png=True)
            if idx >= args.scale_circuits:
                break


def exec_srcgen(hdacv2_board,args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  menv = bmark.get_math_env(args.benchmark)
  hwenv = hwenvs.get_hw_env(args.hw_env)
  recompute = args.recompute
  circ_dir = path_handler.skelt_circ_dir()
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        print('<<<< %s >>>>' % fname)
        circ_bmark,circ_indices,circ_scale_index,circ_opt = \
            path_handler.conc_circ_to_args(fname)
        filename = path_handler.grendel_file(circ_bmark, \
                                            circ_indices, \
                                            circ_scale_index, \
                                            circ_opt,
                                            menv.name,
                                            hwenv.name)

        if path_handler.has_file(filename) and not recompute:
            continue

        conc_circ = ConcCirc.read(hdacv2_board,"%s/%s" % (dirname,fname))
        gren_file = srcgen.generate(path_handler,
                                    hdacv2_board,\
                                    conc_circ,\
                                    menv,
                                    hwenv,
                                    filename=filename)
        gren_file.write(filename)


def exec_graph(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  circ_dir = path_handler.skelt_circ_dir()
  scores = []
  filenames = []
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        circ_bmark,circ_indices,circ_scale_index,opt = \
                                                       path_handler.conc_circ_to_args(fname)

        skelt_circ = path_handler.skelt_circ_file(circ_bmark,
                                                  circ_indices,
                                                  circ_scale_index,
                                                  opt)
        print('<<<< %s >>>>' % fname)
        with open("%s/%s" % (dirname,fname),'r') as fh:
          obj = json.loads(fh.read())
          conc_circ = ConcCirc.from_json(hdacv2_board, \
                                                  obj)
          '''
          methods = ['interval','scaled-interval', \
                         'gen-delay','prop-delay', \
                         'scale-factor','delay-mismatch', \
                         'gen-noise','prop-noise',\
                         'gen-bias','prop-bias']
          '''

          methods = ['gen-noise', 'prop-noise', 'scaled-interval','snr']
          for method in methods:

            filename = path_handler.skelt_graph_file(circ_bmark,
                                                     circ_indices,
                                                     circ_scale_index,
                                                     "%s-%s" % (opt,method))
            conc_circ.write_graph(filename,\
                                  write_png=True,\
                                  color_method=method)

def exec_skelter_existing(hdacv2_board,args):
    path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
    circ_dir = path_handler.conc_circ_dir()
    recompute = args.recompute
    if recompute:
        return

    for dirname, subdirlist, filelist in os.walk(circ_dir):
        for fname in filelist:
            if fname.endswith('.circ'):
                circ_bmark,circ_indices,circ_scale_index,opt = \
                                    path_handler.conc_circ_to_args(fname)

                skelt_circ = path_handler.skelt_circ_file(circ_bmark,
                                                        circ_indices,
                                                        circ_scale_index,
                                                        opt)
                if path_handler.has_file(skelt_circ):
                    continue

                with open("%s/%s" % (dirname,fname),'r') as fh:
                    obj = json.loads(fh.read())
                    conc_circ = ConcCirc.from_json(hdacv2_board, \
                                                            obj)
                    if conc_circ.has_physical_model():
                        print('<<<< %s >>>>' % fname)

                        filename = path_handler.skelt_circ_file(circ_bmark,
                                                            circ_indices,
                                                            circ_scale_index,
                                                            opt)
                        src = "%s/%s" % (dirname,fname)
                        dest = filename
                        shutil.copyfile(src,dest)

def exec_skelter(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  circ_dir = path_handler.conc_circ_dir()
  recompute = args.recompute
  exec_skelter_existing(hdacv2_board,args)
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        circ_bmark,circ_indices,circ_scale_index,opt = \
                            path_handler.conc_circ_to_args(fname)

        skelt_circ = path_handler.skelt_circ_file(circ_bmark,
                                                  circ_indices,
                                                  circ_scale_index,
                                                  opt)
        if path_handler.has_file(skelt_circ)  \
           and not recompute:
          continue

        print('<<<< %s >>>>' % fname)
        with open("%s/%s" % (dirname,fname),'r') as fh:
          obj = json.loads(fh.read())
          conc_circ = ConcCirc.from_json(hdacv2_board, \
                                                  obj)
          if recompute:
              skelter.clear(conc_circ)
          skelter.execute(conc_circ)
          filename = path_handler.skelt_circ_file(circ_bmark,
                                                  circ_indices,
                                                  circ_scale_index,
                                                  opt)
          conc_circ.write_circuit(filename)
