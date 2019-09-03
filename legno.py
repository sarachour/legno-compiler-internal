import sys
import os
import numpy as np
import util.paths as paths


from compiler import  simulator
from hwlib.adp import AnalogDeviceProg

import argparse

import compiler.legno_util as legno_util

#import conc
#import srcgen



parser = argparse.ArgumentParser(description='Legno compiler.')
parser.add_argument('--subset', default="unrestricted",
                    help='component subset to use for compilation')


subparsers = parser.add_subparsers(dest='subparser_name',
                                   help='compilers/compilation passes.')

lgraph_subp = subparsers.add_parser('lgraph', help='generate circuit')
lgraph_subp.add_argument('--simulate', action="store_true",
                       help="ignore resource constraints while compiling.")
lgraph_subp.add_argument('--xforms', type=int,default=3,
                       help='number of abs circuits to generate.')
lgraph_subp.add_argument('--abs-circuits', type=int,default=100,
                       help='number of abs circuits to generate.')
lgraph_subp.add_argument('--conc-circuits', type=int,default=3,
                       help='number of conc circuits to generate.')
lgraph_subp.add_argument('--max-circuits', type=int,default=5,
                       help='maximum number of circuits to generate.')


lgraph_subp.add_argument('program', type=str,help='benchmark to compile')

lscale_subp = subparsers.add_parser('lscale', \
                                   help='scale circuit parameters.')
lscale_subp.add_argument('--model', default="physical",
                        help='use physical models to inform constraints.')
lscale_subp.add_argument('--scale-circuits', type=int,default=5, \
                       help='number of scaled circuits to generate.')
lscale_subp.add_argument('--digital-error', type=float, default=0.04, \
                        help='do performance sweep.')
lscale_subp.add_argument('--analog-error',type=float,default=0.04, \
                        help='do performance sweep.')
lscale_subp.add_argument('--search',action="store_true")
lscale_subp.add_argument('program', type=str,help='benchmark to compile')

lscale_subp.add_argument("--max-freq", type=float, \
                         help="maximum frequency in Khz")

graph_subp = subparsers.add_parser('graph', \
                                   help='emit debugging graph.')
graph_subp.add_argument('--circ', type=str, \
                        help='do performance sweep.')


gren_subp = subparsers.add_parser('srcgen', help='generate grendel scriot.')
gren_subp.add_argument('hw_env', type=str, \
                        help='hardware environment')
gren_subp.add_argument('--recompute', action='store_true',
                       help='recompute.')
gren_subp.add_argument('--trials', type=int, default=3,
                       help='compute trials.')
gren_subp.add_argument('program', type=str,help='benchmark to compile')


sim_subp = subparsers.add_parser('simulate', help='simulate circuit.')
sim_subp.add_argument('conc_circ', help='simulate concrete circuit.')


args = parser.parse_args()

#from hwlib.hcdc.hcdcv2_4 import make_board
#from hwlib.hcdc.globals import HCDCSubset
#subset = HCDCSubset(args.subset)
#hdacv2_board = make_board(subset,load_conns=True)
#args.bmark_dir = subset.value

if args.subparser_name == "lgraph":
    legno_util.exec_lgraph(args)

elif args.subparser_name == "lscale":
    legno_util.exec_lscale(args)

elif args.subparser_name == "srcgen":
   legno_util.exec_srcgen(args)

elif args.subparser_name == "graph":
   legno_util.exec_graph(args)

elif args.subparser_name == "simulate":
   simulator.simulate(args.conc_circ, \
                      args.program)
