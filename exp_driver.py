import argparse
from scripts.expdriver_db import ExpDriverDB

parser = argparse.ArgumentParser(description='toplevel chip runner.')

subparsers = parser.add_subparsers(dest='subparser_name',
                                   help='compilers/compilation passes.')

scan_subp = subparsers.add_parser('scan', help='scan for new grendel scripts')
list_subp = subparsers.add_parser('list', help='list database entries')
list_subp.add_argument('--prog', type=str,
                       help='prog to run.')
list_subp.add_argument('--obj', type=str,
                       help='objective function to run.')


del_subp = subparsers.add_parser('clear', help='delete a benchmark/opt-run')
del_subp.add_argument('--prog', type=str,
                       help='benchmark to delete.')
del_subp.add_argument('--obj', type=str,
                       help='optimization objective function to delete.')

run_subp = subparsers.add_parser('run', help='run any pending grendel scripts')
run_subp.add_argument('--calibrate', action="store_true",
                       help='calibrate.')
run_subp.add_argument('--email', type=str,
                       help='email address.')
run_subp.add_argument('--native', action='store_true',
                       help='use ttyACM0.')
run_subp.add_argument('--prog', type=str,
                       help='prog to run.')
run_subp.add_argument('--subset', type=str,
                       help='prog to run.')
run_subp.add_argument('--model', type=str,
                       help='model to run.')
run_subp.add_argument('--obj', type=str,
                       help='objective function to run.')


analyze_subp = subparsers.add_parser('analyze', help='run any pending grendel scripts')
analyze_subp.add_argument('--recompute-params', action='store_true',
                       help='.')
analyze_subp.add_argument('--recompute-quality', action='store_true',
                       help='.')
analyze_subp.add_argument('--monitor', action='store_true',
                       help='.')
analyze_subp.add_argument('--prog', type=str,
                       help='.')
analyze_subp.add_argument('--subset', type=str,
                       help='.')
analyze_subp.add_argument('--model', type=str,
                       help='model to run.')
analyze_subp.add_argument('--obj', type=str,
                       help='objective function to run.')



visualize_subp = subparsers.add_parser('visualize', help='produce graphs.')
visualize_subp.add_argument('type', help='visualization type [rank-vs-quality,correlation,etc]')


args = parser.parse_args()

if args.subparser_name == "scan":
  db = ExpDriverDB()
  print("=== added ===")
  for exp in db.scan():
    print(exp)

  db.close()
  db.open()

elif args.subparser_name == "list":
  import scripts.analyze_experiments as analyze
  db = ExpDriverDB()
  print("=== all entries ===")
  for entry in db.experiment_tbl.get_all():
    if entry.program != args.prog and not args.prog is None:
      continue
    if entry.obj != args.obj and not args.obj is None:
      continue
    print(entry)
    analyze.rank(entry)

elif args.subparser_name == "clear":
  db = ExpDriverDB()
  print("==== deleted ====")
  entries = list(db.experiment_tbl.get_all())
  for entry in entries:
    if (entry.program == args.prog or args.prog is None) and \
       (entry.obj == args.obj or args.obj is None):
      print(entry)
      entry.delete()

elif args.subparser_name == 'run':
  import scripts.run_experiments as runchip
  runchip.execute(args)

elif args.subparser_name == 'analyze':
  import scripts.analyze_experiments as analyze
  analyze.execute(args)

elif args.subparser_name == 'visualize':
  import scripts.visualize_experiments as visualize
  visualize.execute(args)
