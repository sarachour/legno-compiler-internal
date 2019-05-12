import argparse
import itertools
import numpy as np
import util.config as CONFIG

stmts = []
signs = ["+","-"]
ranges = ["l","m","h"]
ranges_mh = ["m","h"]
whitelist = []

def enq(st):
  stmts.append(st)

def populate_whitelist(filename):
  keys = ["chip","tile","slice","index"]
  with open(filename,'r') as fh:
    for line in fh:
      values = line.strip().split()
      assert(len(values) == 4)
      entry = dict(zip(keys,map(lambda v: int(v), values)))
      handle = "{chip}.{tile}.{slice}.{index}".format(**entry)
      whitelist.append(handle)

def in_whitelist(row):
  handle = "{chip}.{tile}.{slice}.{index}".format(**row)
  if len(whitelist) == 0:
    return True

  return handle in whitelist

def range_to_coeff(rangename):
  if rangename == "m":
    return 1.0
  elif rangename == "l":
    return 0.1
  elif rangename == "h":
    return 10.0

def build_fanouts(args,row):
  # fanout component
  for s0,s1,s2 in itertools.product(*[signs,signs,signs]):
    for third in ['three','two']:
      for rangetype in ranges_mh:
        data = dict(row.items())
        data['range'] = rangetype
        data['sign0'] = s0
        data['sign1'] = s1
        data['sign2'] = s2
        data['third'] = third
        data['cmd'] = 'calibrate' if args.calibrate else 'get_state'
        cmd = "use_fanout {chip} {tile} {slice} {index} "+ \
            "sgn {sign0} {sign1} {sign2} rng {range} {third} update"
        enq(cmd.format(**data))
        enq("{cmd} fanout {chip} {tile} {slice} {index}".format(**data))


def build_values(args):
  if args.sweep:
    n = args.n
    return list(np.arange(-0.98,0.98,(0.98*2)/float(n)));
  else:
    return [0.98]

def build_vgas(args,row):
  for in0range,outrange in \
      itertools.product(*[ranges,ranges]):
    for value in build_values(args):
      data = dict(row)
      data['in0rng'] = in0range
      data['outrng'] = outrange
      data['gain'] = value
      data['cmd'] = 'calibrate' if args.calibrate \
                    else 'get_state'
      coeff = range_to_coeff(outrange)/range_to_coeff(in0range)
      if coeff > 100.0:
        continue
      enq("use_mult {chip} {tile} {slice} {index} val {gain} rng {in0rng} {outrng} update".format(**data))
      enq("{cmd} mult {chip} {tile} {slice} {index}".format(**data))


def build_integrators(args,row):
  if(row['index'] != 0):
    return

  for in0range,outrange in \
      itertools.product(*[ranges,ranges]):
    for sgn in signs:
      for value in build_values(args):
        data = dict(row)
        data['in0rng'] = in0range
        data['outrng'] = outrange
        data['init'] = value
        data['sign'] = sgn
        data['cmd'] = 'calibrate' if args.calibrate \
                      else 'get_state'
        coeff = range_to_coeff(outrange)/range_to_coeff(in0range)
        if coeff > 100.0:
          continue
        enq("use_integ {chip} {tile} {slice} sgn {sign} val {init} rng {in0rng} {outrng} debug update".format(**data))
        enq("{cmd} integ {chip} {tile} {slice} {index}".format(**data))


def build_mults(args,row):
  for in0range,in1range,outrange in \
      itertools.product(*[ranges,ranges,ranges]):
    data = dict(row)
    data['in0rng'] = in0range
    data['in1rng'] = in1range
    data['outrng'] = outrange
    data['cmd'] = 'calibrate' if args.calibrate \
                  else 'get_state'
    in_coeff = range_to_coeff(in0range)*range_to_coeff(in1range)
    coeff = range_to_coeff(outrange)/in_coeff
    if coeff > 100.0:
      continue
    enq("use_mult {chip} {tile} {slice} {index} rng {in0rng} {in1rng} {outrng} update".format(**data))
    enq("{cmd} mult {chip} {tile} {slice} {index}".format(**data))


def build_dacs_mem(args,row):
  if row['index'] != 0 or \
     (row['slice'] != 0 and row['slice'] != 2):
    return

  for inrange in ranges_mh:
    for val in build_values(args):
      data = dict(row)
      data['inrng'] = inrange
      data['value'] = val
      data['cmd'] = 'calibrate' if args.calibrate \
                    else 'get_state'
      enq("use_dac {chip} {tile} {slice} src mem sgn + val {value} rng {inrng} update".format(**data))
      enq("{cmd} dac {chip} {tile} {slice} {index}".format(**data))

def build_dacs_lut(args,row):
  if row['index'] != 0 or \
     (row['slice'] != 0 and row['slice'] != 2):
    return

  for inrange in ranges_mh:
    for lut in ["lut0","lut1"]:
      data = dict(row)
      data['inrng'] = inrange
      data['src'] = lut
      data['cmd'] = 'calibrate' if args.calibrate \
                    else 'get_state'
      enq("use_dac {chip} {tile} {slice} src {src} sgn + val 0.0 rng {inrng} update".format(**data))
      enq("{cmd} dac {chip} {tile} {slice} {index}".format(**data))


def build_adcs(args,row):
  if row['index'] != 0 or \
     (row['slice'] != 0 and row['slice'] != 2):
    return

  for inrange in ranges_mh:
    data = dict(row)
    data['inrng'] = inrange
    data['cmd'] = 'calibrate' if args.calibrate \
                  else 'get_state'
    enq("use_adc {chip} {tile} {slice} rng {inrng} update".format(**data))
    enq("{cmd} adc {chip} {tile} {slice} {index}".format(**data))

def build_testfile(args):
  row = {}
  for chipno in range(0,2):
    row['chip'] = chipno
    for tileno in range(0,4):
      row['tile'] = tileno
      for sliceno in range(0,4):
        row['slice'] = sliceno
        for indexno in range(0,2):
          row['index'] = indexno

          if not in_whitelist(row):
            continue

          build_fanouts(args,row)
          build_mults(args,row)
          build_vgas(args,row)
          build_integrators(args,row)
          build_adcs(args,row)
          build_dacs_mem(args,row)
          build_dacs_lut(args,row)

  with open('test_chip.grendel','w') as fh:
    for st in stmts:
      fh.write("%s\n" % st)

parser = argparse.ArgumentParser()
parser.add_argument("--calibrate", action='store_true',help="calibrate instead of getting codes.")
parser.add_argument("--sweep", action='store_true',help="perform value sweeps.")
parser.add_argument("--n", type=int, default=10,help="number of segments.")
parser.add_argument("--whitelist", type=str,help="whitelist of slices to look at.")
parser.add_argument("--db",type=str,default="state.db", \
                    help="database to write")

args = parser.parse_args()

CONFIG.STATE_DB = args.db

if args.whitelist != None:
  populate_whitelist(args.whitelist)

print("building calibration file")
build_testfile(args)
