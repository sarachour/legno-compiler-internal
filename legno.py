import sys
import os
import numpy as np
import bmark.diffeqs as bmark
import bmark.menvs as menvs
import util.paths as paths


from compiler import arco, jaunt, srcgen, execprog, skelter
from chip.conc import ConcCirc

import argparse

import compiler.legno_util as legno_util

#import conc
#import srcgen



parser = argparse.ArgumentParser(description='Legno compiler.')
parser.add_argument('--standard',action="store_true",
                    help='limit compiler to standard set of components')
parser.add_argument('benchmark', type=str,help='benchmark to compile')
parser.add_argument('--bmark-dir', type=str,default='default',
                       help='directory to output files to.')


subparsers = parser.add_subparsers(dest='subparser_name',
                                   help='compilers/compilation passes.')

arco_subp = subparsers.add_parser('arco', help='generate circuit')
arco_subp.add_argument('--simulate', action="store_true",
                       help="ignore resource constraints while compiling.")
arco_subp.add_argument('--xforms', type=int,default=3,
                       help='number of abs circuits to generate.')
arco_subp.add_argument('--abs-circuits', type=int,default=100,
                       help='number of abs circuits to generate.')
arco_subp.add_argument('--conc-circuits', type=int,default=3,
                       help='number of conc circuits to generate.')


jaunt_subp = subparsers.add_parser('jaunt', \
                                   help='scale circuit parameters.')
jaunt_subp.add_argument('--physical', action='store_true', \
                        help='use physical models to inform constraints.')
jaunt_subp.add_argument('--sweep', action='store_true', \
                        help='do performance sweep.')
jaunt_subp.add_argument('--scale-circuits', type=int,default=15, \
                       help='number of scaled circuits to generate.')


skelt_subp = subparsers.add_parser('skelter', help='perform any bias correction from physical model')
skelt_subp.add_argument('--recompute', action='store_true',
                       help='recompute skelter.')

graph_subp = subparsers.add_parser('graph', help='generate graphs for noise analysis')
graph_subp.add_argument('--circ', help='circuit.')

gren_subp = subparsers.add_parser('srcgen', help='generate grendel.')
gren_subp.add_argument('hw_env', type=str, \
                        help='hardware environment')
gren_subp.add_argument('--recompute', action='store_true',
                       help='recompute.')
gren_subp.add_argument('--trials', type=int, default=3,
                       help='compute trials.')



args = parser.parse_args()
prog = bmark.get_prog(args.benchmark)

from chip.hcdc.hcdcv2_4 import make_board
from chip.hcdc.globals import HCDCSubset
if args.standard:
    hdacv2_board = make_board(HCDCSubset.STANDARD)
else:
    hdacv2_board = make_board(HCDCSubset.UNRESTRICTED)


if args.subparser_name == "arco":
    legno_util.exec_arco(hdacv2_board, args)

elif args.subparser_name == "graph":
    legno_util.exec_graph(hdacv2_board,args)

elif args.subparser_name == "skelter":
    legno_util.exec_skelter(hdacv2_board,args)


elif args.subparser_name == "jaunt":
    if args.physical or args.sweep:
        legno_util.exec_jaunt_phys(hdacv2_board,args)

    if not args.physical and not args.sweep:
        legno_util.exec_jaunt(hdacv2_board,args)

elif args.subparser_name == "srcgen":
   legno_util.exec_srcgen(hdacv2_board,args)
