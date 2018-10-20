import pstats
import sys

stat_file = sys.argv[1]
p = pstats.Stats(stat_file)

p.sort_stats('cumtime').print_stats()
