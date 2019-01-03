import sys
import os

sys.path.insert(0,os.path.abspath("lab_bench"))

from compiler import arco, jaunt, srcgen, execprog
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
jaunt_subp.add_argument('--scale-circuits', type=int,default=3,
                       help='number of scaled circuits to generate.')


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

if args.subparser_name == "arco":
    from chip.hcdc import board as hdacv2_board

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

elif args.subparser_name == "jaunt":
    from chip.hcdc import board as hdacv2_board

    circ_dir = path_handler.abs_circ_dir()
    for dirname, subdirlist, filelist in os.walk(circ_dir):
        for fname in filelist:
            if fname.endswith('.circ'):
                print('<<<< %s >>>>' % fname)
                with open("%s/%s" % (dirname,fname),'r') as fh:
                    obj = json.loads(fh.read())
                    circ_bmark,circ_indices = path_handler.abs_circ_to_args(fname)
                    conc_circ = ConcCirc.from_json(hdacv2_board, \
                                               obj)
                    n_scaled = 0
                    for scale_circ in jaunt.scale(conc_circ, \
                                                  noise_analysis=args.noise):
                        filename = path_handler.conc_circ_file(circ_bmark,
                                                               circ_indices,
                                                               n_scaled)
                        scale_circ.write_circuit(filename)
                        filename = path_handler.conc_graph_file(circ_bmark,
                                                                circ_indices,
                                                                n_scaled)
                        scale_circ.write_graph(filename,write_png=True)
                        n_scaled += 1
                        if n_scaled >= args.scale_circuits:
                            break

elif args.subparser_name == "execprog":
   from chip.hcdc import board as hdacv2_board
   prog = bmark.get_prog(args.benchmark)
   menv = menvs.get_math_env(args.math_env)
   execprog.execute(path_handler,
                    prog,
                    menv)

elif args.subparser_name == "srcgen":
   from chip.hcdc import board as hdacv2_board
   menv = menvs.get_math_env(args.math_env)
   hwenv = hwenvs.get_hw_env(args.hw_env)
   circ_dir = path_handler.conc_circ_dir()
   for dirname, subdirlist, filelist in os.walk(circ_dir):
       for fname in filelist:
           if fname.endswith('.circ'):
               print('<<<< %s >>>>' % fname)
               with open("%s/%s" % (dirname,fname),'r') as fh:
                   obj = json.loads(fh.read())
                   circ_bmark,circ_indices,circ_scale_index = \
                    path_handler.conc_circ_to_args(fname)
                   conc_circ = ConcCirc.from_json(hdacv2_board, \
                                                  obj)
                   filename = path_handler.grendel_file(circ_bmark, \
                                                        circ_indices, \
                                                        circ_scale_index, \
                                                        menv.name,
                                                        hwenv.name)
                   gren_file = srcgen.generate(path_handler,
                                               hdacv2_board,\
                                               conc_circ,\
                                               menv,
                                               hwenv,
                                               filename=filename)
                   gren_file.write(filename)
