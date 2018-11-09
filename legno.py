from compiler import arco, jaunt
import argparse
import os
import time

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

subparsers = parser.add_subparsers(dest='subparser_name',
                                   help='compilers/compilation passes.')

arco_subp = subparsers.add_parser('arco', help='generate circuit')
arco_subp.add_argument('benchmark', type=str,help='benchmark to compile')
arco_subp.add_argument('--xforms', type=int,default=3,
                       help='number of abs circuits to generate.')
arco_subp.add_argument('--abs-circuits', type=int,default=100,
                       help='number of abs circuits to generate.')
arco_subp.add_argument('--conc-circuits', type=int,default=3,
                       help='number of conc circuits to generate.')
arco_subp.add_argument('--output-dir', type=str,default='circs',
                       help='output directory to output files to.')



jaunt_subp = subparsers.add_parser('jaunt', help='scale circuit parameters.')
jaunt_subp.add_argument('benchmark', type=str,help='benchmark to compile')
jaunt_subp.add_argument('--experiment', type=str,help='experiment to run')
jaunt_subp.add_argument('--input-dir', type=str,help='output directory to output files to.')
jaunt_subp.add_argument('--noise', type=str,help='perform noise analysis.')


args = parser.parse_args()

OUTDIR = "outputs"

if not os.path.exists(OUTDIR):
    os.mkdir(OUTDIR)

if not os.path.exists("%s/%s" % (OUTDIR,args.output_dir)):
    os.mkdir("%s/%s" % (OUTDIR,args.output_dir))

if args.subparser_name == "arco":
    from chip.hcdc import board as hdacv2_board
    import bmark.bmarks as bmark

    problem = bmark.get_bmark(args.benchmark)

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    for indices,conc_circ,abs_circ in \
        arco.compile(hdacv2_board,
                               problem,
                               depth=args.xforms,
                               max_abs_circs=args.abs_circuits,
                               max_conc_circs=args.conc_circuits):
        index_str = "_".join(map(lambda ind : str(ind),indices))
        circ_file= "%s_%s.circ" % (args.benchmark,index_str)
        dot_file = "%s_%s.dot" % (args.benchmark,index_str)
        filedir = "%s/%s/%s" % (OUTDIR,args.output_dir,circ_file)
        conc_circ.write_circuit(filedir)
        filedir = "%s/%s/%s" % (OUTDIR,args.output_dir,dot_file)
        conc_circ.write_graph(filedir,write_png=True)
        time.sleep(1)
