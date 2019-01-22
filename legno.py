import sys
import os
import numpy as np

sys.path.insert(0,os.path.abspath("lab_bench"))

from compiler import arco, jaunt, srcgen, execprog, skelter
from chip.conc import ConcCirc

import argparse
import os
import time
from util import paths
import json

import bmark.menvs as menvs
import bmark.hwenvs as hwenvs
import bmark.diffeqs as bmark

#import conc
#import srcgen

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



parser = argparse.ArgumentParser(description='Legno compiler.')
parser.add_argument('benchmark', type=str,help='benchmark to compile')
parser.add_argument('--bmark-dir', type=str,default='default',
                       help='directory to output files to.')


subparsers = parser.add_subparsers(dest='subparser_name',
                                   help='compilers/compilation passes.')

arco_subp = subparsers.add_parser('arco', help='generate circuit')
arco_subp.add_argument('--xforms', type=int,default=3,
                       help='number of abs circuits to generate.')
arco_subp.add_argument('--abs-circuits', type=int,default=100,
                       help='number of abs circuits to generate.')
arco_subp.add_argument('--conc-circuits', type=int,default=3,
                       help='number of conc circuits to generate.')


jaunt_subp = subparsers.add_parser('jaunt', help='scale circuit parameters.')
jaunt_subp.add_argument('--noise', type=str,help='perform noise analysis.')
jaunt_subp.add_argument('--scale-circuits', type=int,default=15,
                       help='number of scaled circuits to generate.')


ref_subp = subparsers.add_parser('skelter', help='perform noise analysis')
ref_subp.add_argument('--math-env', type=str,default='t20',
                       help='math environment.')
ref_subp.add_argument('--hw-env', type=str,default='default', \
                        help='hardware environment')
ref_subp.add_argument('--gen-script-list', action='store_true',
                        help='generate a script list')




ref_subp = subparsers.add_parser('execprog', help='compute reference signal')
ref_subp.add_argument('math_env', type=str,
                       help='math environment.')



gren_subp = subparsers.add_parser('srcgen', help='generate grendel.')
gren_subp.add_argument('math_env', type=str,
                       help='math environment.')
gren_subp.add_argument('hw_env', type=str, \
                        help='hardware environment')

args = parser.parse_args()

path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)

from chip.hcdc.hcdcv2_4 import board as hdacv2_board

if args.subparser_name == "arco":
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

elif args.subparser_name == "skelter":
    circ_dir = path_handler.conc_circ_dir()
    scores = []
    filenames = []
    for dirname, subdirlist, filelist in os.walk(circ_dir):
        for fname in filelist:
           if fname.endswith('.circ'):
               print('<<<< %s >>>>' % fname)
               with open("%s/%s" % (dirname,fname),'r') as fh:
                   obj = json.loads(fh.read())
                   conc_circ = ConcCirc.from_json(hdacv2_board, \
                                                  obj)

                   score = skelter.execute(conc_circ)
                   scores.append(score)
                   filenames.append(fname)


    sorted_indices = np.argsort(scores)
    with open('scores.txt','w') as fh:
        for ind in sorted_indices:
            line = "%s\t\t %s" % (scores[ind], filenames[ind])
            fh.write("%s\n" % line)
            print(line)

    if args.gen_script_list:
        menv = args.math_env
        hwenv = args.hw_env
        subinds = np.random.choice(sorted_indices,15)
        subscores = list(map(lambda i: scores[i], subinds))
        sorted_subinds = map(lambda i: subinds[i], np.argsort(subscores)[::-1])

        files = []
        for ind in sorted_subinds:
            score = scores[ind]
            conc_filename = filenames[ind]
            circ_bmark,circ_indices,circ_scale_index,opt = \
                    path_handler.conc_circ_to_args(conc_filename)
            gren_filename = path_handler.grendel_file(circ_bmark, \
                                                      circ_indices, \
                                                      circ_scale_index, \
                                                      opt, \
                                                      menv,
                                                      hwenv)
            print(gren_filename,score)
            assert(path_handler.has_file(gren_filename))
            files.append((gren_filename,score))

        script_file = "run_%s.grendel-list" % args.benchmark
        with open(script_file,'w') as fh:
            for filename,score in files:
                fh.write("# %f\n" % score)
                fh.write("%s\n" % filename)


elif args.subparser_name == "jaunt":
    prog = bmark.get_prog(args.benchmark)
    circ_dir = path_handler.abs_circ_dir()
    for dirname, subdirlist, filelist in os.walk(circ_dir):
        for fname in filelist:
            if fname.endswith('.circ'):
                circ_bmark,circ_indices = path_handler \
                                          .abs_circ_to_args(fname)
                print('<<<< %s >>>>' % fname)
                with open("%s/%s" % (dirname,fname),'r') as fh:
                    obj = json.loads(fh.read())
                    conc_circ = ConcCirc.from_json(hdacv2_board, \
                                               obj)
                    n_scaled = 0
                    for idx,(opt,scale_circ) in enumerate(jaunt.scale(prog,
                                                  conc_circ, \
                                                  noise_analysis=args.noise)):

                        filename = path_handler.conc_circ_file(circ_bmark,
                                                               circ_indices,
                                                               idx,
                                                               opt)
                        scale_circ.write_circuit(filename)

                        filename = path_handler.conc_graph_file(circ_bmark,
                                                                circ_indices,
                                                                n_scaled,
                                                                opt)
                        scale_circ.write_graph(filename,write_png=True)
                        if idx >= args.scale_circuits:
                            break

elif args.subparser_name == "execprog":
   prog = bmark.get_prog(args.benchmark)
   menv = menvs.get_math_env(args.math_env)
   execprog.execute(path_handler,
                    prog,
                    menv)

elif args.subparser_name == "srcgen":
   menv = menvs.get_math_env(args.math_env)
   hwenv = hwenvs.get_hw_env(args.hw_env)
   circ_dir = path_handler.conc_circ_dir()
   for dirname, subdirlist, filelist in os.walk(circ_dir):
       for fname in filelist:
           if fname.endswith('.circ'):
               print('<<<< %s >>>>' % fname)
               with open("%s/%s" % (dirname,fname),'r') as fh:
                   circ_bmark,circ_indices,circ_scale_index,circ_opt = \
                    path_handler.conc_circ_to_args(fname)
                   filename = path_handler.grendel_file(circ_bmark, \
                                                        circ_indices, \
                                                        circ_scale_index, \
                                                        circ_opt,
                                                        menv.name,
                                                        hwenv.name)

                   if path_handler.has_file(filename):
                       continue

                   obj = json.loads(fh.read())
                   conc_circ = ConcCirc.from_json(hdacv2_board, \
                                                  obj)
                   gren_file = srcgen.generate(path_handler,
                                               hdacv2_board,\
                                               conc_circ,\
                                               menv,
                                               hwenv,
                                               filename=filename)
                   gren_file.write(filename)
