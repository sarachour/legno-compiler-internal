
# grendel generates scripts to exercise a component.

parser = argparse.ArgumentParser()
parser.add_argument("--inputs", type=int,help="number of inputs.")
parser.add_argument("--block",type=str,help="block to exercise")
parser.add_argument("--chip", type=int,help="chip number.")
parser.add_argument("--tile", type=int,help="tile number.")
parser.add_argument("--slice", type=int,help="slice number.")
parser.add_argument("--index", type=int,help="index number.")

args = parser.parse_args()
