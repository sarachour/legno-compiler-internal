from compiler import arco, jaunt
from chip.conc import ConcCirc

import argparse
import os
import time
from util import paths
import json

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

gren_subp = subparsers.add_parser('gen_grendel', help='generate grendel.')
gren_subp.add_argument('benchmark', type=str,help='benchmark to compile')
gren_subp.add_argument('--input-dir', type=str,help='output directory to output files to.')
gren_subp.add_argument('--output-dir', type=str,default='default',
                       help='output directory to output files to.')
gren_subp.add_argument('--experiment', type=str,default='default',
                       help='output directory to output files to.')

args = parser.parse_args()

path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)

if args.subparser_name == "arco":
    from chip.hcdc import board as hdacv2_board
    import bmark.bmarks as bmark

    problem = bmark.get_bmark(args.benchmark)

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
    import bmark.bmarks as bmark

    circ_dir = path_handler.abs_circ_dir()
    for dirname, subdirlist, filelist in os.walk(circ_dir):
        for fname in filelist:
            if fname.endswith('.circ'):
                print('%s' % fname)
                with open("%s/%s" % (dirname,fname),'r') as fh:
                    obj = json.loads(fh.read())
                    conc_circ = ConcCirc.from_json(hdacv2_board, \
                                               obj)
                    for scale_circ in jaunt.scale(conc_circ, \
                                                  noise_analysis=args.noise):
                        raise Exception("emit scaled")

elif args.subparser_name == "gen":
    for dirname, subdirlist, filelist in os.walk(args.input_dir):
        for fname in filelist:
            if fname.endswith('.circ'):
                print('%s' % fname)
                with open("%s/%s" % (dirname,fname),'r') as fh:
                    text = fh.read()
                    ccirc = conccirc.from_json(text)
                    raise Exception("generate grendel")
