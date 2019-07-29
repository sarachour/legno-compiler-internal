from chip.block import Block,BlockType
from chip.config import  Config
import chip.abs as acirc
import chip.conc as ccirc
import sys
import itertools
import logging
import compiler.arco_pass.util as arco_util
import compiler.arco_pass.route_ilp as route_ilp

def route(board,prob,node_map,max_failures=None,max_resolutions=None):
    #sys.setrecursionlimit(1000)
    yield route_ilp.route(board,prob,node_map)
