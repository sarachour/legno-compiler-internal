import argparse
import scripts.run_experiments as runchip
import scripts.analyze_experiments as analyze
import scripts.visualize_experiments as visualize
from scripts.db import ExperimentDB

parser = argparse.ArgumentParser(description='toplevel chip runner.')

subparsers = parser.add_subparsers(dest='subparser_name',
                                   help='compilers/compilation passes.')


scan_subp = subparsers.add_parser('scan', help='scan for new grendel scripts')

run_subp = subparsers.add_parser('run', help='run any pending grendel scripts')
run_subp.add_argument('--ip', type=str,
                       help='oscilloscope ip.')
run_subp.add_argument('--email', type=str,
                       help='email address.')
run_subp.add_argument('--native', action='store_true',
                       help='use ttyACM0.')

analyze_subp = subparsers.add_parser('analyze', help='run any pending grendel scripts')
analyze_subp.add_argument('--recompute-rank', action='store_true',
                       help='.')
analyze_subp.add_argument('--recompute-runtime', action='store_true',
                       help='.')
analyze_subp.add_argument('--recompute-quality', action='store_true',
                       help='.')

visualize_subp = subparsers.add_parser('visualize', help='produce graphs.')
visualize_subp.add_argument('type', help='visualization type [rank-vs-quality,correlation,etc]')

args = parser.parse_args()


if args.subparser_name == "scan":
  db = ExperimentDB()
  db.scan()

elif args.subparser_name == 'run':
  runchip.execute(args)

elif args.subparser_name == 'analyze':
  analyze.execute(args)

elif args.subparser_name == 'visualize':
  visualize.execute(args)
