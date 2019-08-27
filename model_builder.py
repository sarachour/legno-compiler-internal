import argparse
import sys
import os
import shutil
import util.config as CONFIG
from chip.model import ModelDB
import json
import argparse
from chip.hcdc.globals import HCDCSubset
from chip.model import PortModel, ModelDB
from chip.conc import ConcCirc

import compiler.infer_pass.infer_dac as infer_dac
import compiler.infer_pass.infer_adc as infer_adc
import compiler.infer_pass.infer_fanout as infer_fanout
import compiler.infer_pass.infer_integ as infer_integ
import compiler.infer_pass.infer_mult as infer_mult
import compiler.infer_pass.infer_visualize as infer_visualize

from lab_bench.lib.chipcmd.data import CalibType


def build_model(datum):
  blk = datum['metadata']['block']
  if blk == 'dac':
    for model in infer_dac.infer(datum):
      yield model

  elif blk == 'adc':
    for model in infer_adc.infer(datum):
      yield model

  elif blk == 'fanout':
    for model in infer_fanout.infer(datum):
      yield model

  elif blk == 'integ':
    for model in infer_integ.infer(datum):
      yield model

  elif blk == 'mult':
    for model in infer_mult.infer(datum):
      yield model
  else:
    raise Exception("unsupported <%s>" % blk)

def populate_default_models(board):
  print("==== Populate Default Models ===")
  db = ModelDB()
  for blkname in ['tile_in','tile_out', \
                  'chip_in','chip_out', \
                  'ext_chip_in','ext_chip_out']:
    block = board.block(blkname)
    for inst in board.instances_of_block(blkname):
      for port in block.inputs + block.outputs:
        model = PortModel(blkname,inst,port, \
                          comp_mode='*', \
                          scale_mode='*')
        db.put(model)

    for blkname in ['lut']:
      block = board.block(blkname)
      for inst in board.instances_of_block(blkname):
        for port in block.inputs + block.outputs:
          model = PortModel(blkname,inst,port, \
                            comp_mode='*', \
                            scale_mode='*')
          model.bias_uncertainty = 0.0
          model.noise = 0.0
          db.put(model)

def write_models(models):
  if len(models) == 0:
    return

  direc = infer_visualize.get_directory(models[0])
  filename = "model.json"
  path = "%s/%s" % (direc,filename)
  with open(path,'w') as fh:
    for model in models:
      fh.write(str(model))
      fh.write("\n\n")


def infer(args,dump_db=True):
  if args.visualize:
    infer_visualize.DO_PLOTS = True

  infer_visualize.CALIB_MODE = CalibType(args.calib_mode)

  db = ModelDB(CalibType(args.calib_mode))

  if args.populate_crossbars:
    from chip.hcdc.hcdcv2_4 import make_board
    subset = HCDCSubset('unrestricted')
    hdacv2_board = make_board(subset)
    populate_default_models(hdacv2_board)
    sys.exit(0)

  if dump_db:
    cmd = "python3 grendel.py --dump-db calibrate.grendel"
    print(cmd)
    retcode = os.system(cmd)
    if retcode != 0:
      raise Exception("could not dump database: retcode=%d" % retcode)

  filepath = "%s/%s" % (CONFIG.DATASET_DIR,args.calib_mode)
  for dirname, subdirlist, filelist in os.walk(filepath):
    for fname in filelist:
      if fname.endswith('.json'):
        fpath = "%s/%s" % (dirname,fname)
        with open(fpath,'r') as fh:
          obj = json.loads(fh.read())
          for datum in obj:
            models = []
            for m in build_model(datum):
              models.append(m)
              db.put(m)

            write_models(models)

def analyze(args):
  circ = ConcCirc.read(None,args.circ_file)
  db = ModelDB(CalibType(args.calib_mode))
  blacklist = ['tile_in','tile_out', \
               'chip_in','chip_out', \
               'ext_chip_in','ext_chip_out']
  for block,loc,cfg in circ.instances():
    comp_mode = cfg.comp_mode
    scale_mode = cfg.scale_mode
    if block in blacklist:
      continue

    print("===== %s[%s] cm=%s sm=%s" % (block,loc,comp_mode,scale_mode))
    has_models = False
    for model in db.get_by_block(block,loc,comp_mode,scale_mode):
      print(model)
      has_models = True

    if not has_models:
      print("...")
      print("...")
      print("NO MODELS")
      print("...")
      print("...")

parser = argparse.ArgumentParser(description="Model inference engine")

subparsers = parser.add_subparsers(dest='subparser_name',
                                   help='compilers/compilation passes.')


infer_subp = subparsers.add_parser('infer', \
                                   help='scale circuit parameters.')
infer_subp.add_argument('--populate-crossbars',action='store_true',
                    help='insert default models for connection blocks')
infer_subp.add_argument('--visualize',action='store_true',
                    help='emit visualizations for models')
infer_subp.add_argument('--calib-mode',type=str,default='min_error',
                        help='calibration objective function to get datasets for')
analyze_subp = subparsers.add_parser('analyze', \
                              help='return delta models for circuit')
analyze_subp.add_argument('circ_file',
                    help='circ file to analyze')

args = parser.parse_args()


if args.subparser_name == "infer":
  infer(args)

elif args.subparser_name == "analyze":
  analyze(args)
