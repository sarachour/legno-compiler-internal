import sys
import os
import numpy as np
import bmark.diffeqs as bmark
import bmark.menvs as menvs
import util.paths as paths

sys.path.insert(0,os.path.abspath("lab_bench"))

from compiler import arco, jaunt, srcgen, execprog, skelter
from chip.conc import ConcCirc

import argparse

import compiler.legno_util as legno_util

#import conc
#import srcgen



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
jaunt_subp.add_argument('--physical', action='store_true',help='perform noise analysis.')
jaunt_subp.add_argument('--scale-circuits', type=int,default=15,
                       help='number of scaled circuits to generate.')


skelt_subp = subparsers.add_parser('skelter', help='perform noise analysis')
skelt_subp = subparsers.add_parser('graph', help='perform noise analysis')


scriptgen_subp = subparsers.add_parser('scriptgen', help='generate grendel scripts')
scriptgen_subp.add_argument('--math-env', type=str,default='t20',
                       help='math environment.')
scriptgen_subp.add_argument('--hw-env', type=str,default='default', \
                        help='hardware environment')



ref_subp = subparsers.add_parser('execprog', help='compute reference signal')

gren_subp = subparsers.add_parser('srcgen', help='generate grendel.')
gren_subp.add_argument('hw_env', type=str, \
                        help='hardware environment')

args = parser.parse_args()


from chip.hcdc.hcdcv2_4 import board as hdacv2_board

if args.subparser_name == "arco":
    legno_util.exec_arco(hdacv2_board, args)

elif args.subparser_name == "graph":
    legno_util.exec_graph(hdacv2_board,args)

elif args.subparser_name == "skelter":
    legno_util.exec_skelter(hdacv2_board,args)

elif args.subparser_name == 'scriptgen':
    legno_util.exec_scriptgen(hdacv2_board,args)

elif args.subparser_name == "jaunt":
    if args.physical:
        legno_util.exec_jaunt_phys(hdacv2_board,args)
    else:
        legno_util.exec_jaunt(hdacv2_board,args)

elif args.subparser_name == "execprog":
   path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
   prog = bmark.get_prog(args.benchmark)
   menv = menvs.get_math_env(args.math_env)
   execprog.execute(path_handler,
                    prog,
                    menv)

elif args.subparser_name == "srcgen":
   legno_util.exec_srcgen(hdacv2_board,args)
