import bmark.menvs as menvs
import bmark.hwenvs as hwenvs
import bmark.diffeqs as bmark
from util import paths
from compiler import arco, jaunt, srcgen, execprog, skelter
from chip.conc import ConcCirc
import os
import time
import json

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

def exec_ref(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  prog = bmark.get_prog(args.benchmark)
  menv = menvs.get_math_env(args.math_env)
  execprog.execute(path_handler,
                   prog,
                   menv)

def exec_arco(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  problem = bmark.get_prog(args.benchmark)

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

def exec_jaunt_phys(hdacv2_board,args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  prog = bmark.get_prog(args.benchmark)
  circ_dir = path_handler.skelt_circ_dir()
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        circ_bmark,circ_indices,circ_scale_index,circ_opt = \
           path_handler.conc_circ_to_args(fname)

        with open("%s/%s" % (dirname,fname),'r') as fh:
          obj = json.loads(fh.read())
          conc_circ = ConcCirc.from_json(hdacv2_board, \
                                         obj)
          for opt,scaled_circ in jaunt.physical_scale(prog,conc_circ):
            filename = path_handler.conc_circ_file(circ_bmark,
                                                   circ_indices,
                                                   circ_scale_index,
                                                   opt)
            scaled_circ.write_circuit(filename)
            filename = path_handler.conc_graph_file(circ_bmark,
                                                    circ_indices,
                                                    circ_scale_index,
                                                    opt)
            scaled_circ.write_graph(filename,write_png=True)



def exec_jaunt(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  prog = bmark.get_prog(args.benchmark)
  circ_dir = path_handler.abs_circ_dir()
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        circ_bmark,circ_indices = path_handler \
                                  .abs_circ_to_args(fname)
        print('<<<< %s >>>>' % fname)
        with open("%s/%s" % (dirname,fname),'r') as fh:
          obj = json.loads(fh.read())
          conc_circ = ConcCirc.from_json(hdacv2_board, \
                                         obj)
          already_written = True
          for idx,opt in jaunt.files(range(0,args.scale_circuits)):
            filename = path_handler.conc_circ_file(circ_bmark,
                                                   circ_indices,
                                                   idx,
                                                   opt)
            if not path_handler.has_file(filename):
              already_written = False

              if not already_written:
                for idx,(opt,scale_circ) in enumerate(jaunt.scale(prog,
                                                                  conc_circ)):
                  filename = path_handler.conc_circ_file(circ_bmark,
                                                         circ_indices,
                                                         idx,
                                                         opt)
                  scale_circ.write_circuit(filename)
                  filename = path_handler.conc_graph_file(circ_bmark,
                                                          circ_indices,
                                                          idx,
                                                          opt)
                  scale_circ.write_graph(filename,write_png=True)
                  if idx >= args.scale_circuits:
                    break


def exec_srcgen(hdacv2_board,args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  menv = menvs.get_math_env(args.math_env)
  hwenv = hwenvs.get_hw_env(args.hw_env)
  circ_dir = path_handler.skelt_circ_dir()
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        print('<<<< %s >>>>' % fname)
        with open("%s/%s" % (dirname,fname),'r') as fh:
          circ_bmark,circ_indices,circ_scale_index,circ_opt = \
             path_handler.conc_circ_to_args(fname)
          filename = path_handler.grendel_file(circ_bmark, \
                                               circ_indices, \
                                               circ_scale_index, \
                                               circ_opt,
                                               menv.name,
                                               hwenv.name)

          if path_handler.has_file(filename):
            continue

          obj = json.loads(fh.read())
          conc_circ = ConcCirc.from_json(hdacv2_board, \
                                                  obj)
          gren_file = srcgen.generate(path_handler,
                                      hdacv2_board,\
                                      conc_circ,\
                                      menv,
                                      hwenv,
                                      filename=filename)
          gren_file.write(filename)

def exec_scriptgen(hdacv2_board,args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  menv = args.math_env
  hwenv = args.hw_env
  scores = []
  filenames = []
  circ_dir = path_handler.skelt_circ_dir()
  for dirname, subdirlist, filelist in os.walk(circ_dir):
      for fname in filelist:
          if fname.endswith('.circ'):
              print('<<<< %s >>>>' % fname)
              with open("%s/%s" % (dirname,fname),'r') as fh:
                  obj = json.loads(fh.read())
                  conc_circ = ConcCirc.from_json(hdacv2_board, \
                                                obj)
                  score = skelter.rank(conc_circ)
                  scores.append(score)
                  filenames.append(fname)

  sorted_indices = np.argsort(scores)
  script_file = "rank_%s.txt" % args.benchmark
  with open(script_file,'w') as fh:
      for ind in sorted_indices:
          line = "%s\n%s\n" % (scores[ind], filenames[ind])
          fh.write("%s\n" % line)
          print(line)

  subinds = np.random.choice(sorted_indices,15)
  subscores = list(map(lambda i: scores[i], subinds))
  sorted_subinds = map(lambda i: subinds[i], np.argsort(subscores)[::-1])
  sorted_indices = np.argsort(scores)

  files = []
  for ind in sorted_subinds:
      score = scores[ind]
      conc_filename = filenames[ind]
      circ_bmark,circ_indices,circ_scale_index,opt = \
              path_handler.conc_circ_to_args(conc_filename)
      gren_filename = path_handler.grendel_file(circ_bmark, \
                                                  circ_indices, \
                                                  circ_scale_index, \
                                                  opt, \
                                                  menv,
                                                  hwenv)
      print(gren_filename,score)
      assert(path_handler.has_file(gren_filename))
      files.append((gren_filename,score))

  script_file = "batch_%s.grendel-list" % args.benchmark
  with open(script_file,'w') as fh:
      for filename,score in files:
          fh.write("# %f\n" % score)
          fh.write("%s\n" % filename)


def exec_skelter(hdacv2_board, args):
  path_handler = paths.PathHandler(args.bmark_dir,args.benchmark)
  circ_dir = path_handler.conc_circ_dir()
  scores = []
  filenames = []
  for dirname, subdirlist, filelist in os.walk(circ_dir):
    for fname in filelist:
      if fname.endswith('.circ'):
        circ_bmark,circ_indices,circ_scale_index,opt = \
                                                       path_handler.conc_circ_to_args(fname)

        skelt_circ = path_handler.skelt_circ_file(circ_bmark,
                                                  circ_indices,
                                                  circ_scale_index,
                                                  opt)
        if path_handler.has_file(skelt_circ):
          continue

        print('<<<< %s >>>>' % fname)
        with open("%s/%s" % (dirname,fname),'r') as fh:
          obj = json.loads(fh.read())
          conc_circ = ConcCirc.from_json(hdacv2_board, \
                                                  obj)
          skelter.execute(conc_circ)
          for method in ['interval','scaled-interval', \
                         'gen-delay','prop-delay', \
                         'scale-factor','delay-mismatch', \
                         'gen-noise','prop-noise',\
                         'gen-bias','prop-bias']:

            filename = path_handler.skelt_graph_file(circ_bmark,
                                                     circ_indices,
                                                     circ_scale_index,
                                                     "%s-%s" % (opt,method))
            conc_circ.write_graph(filename,\
                                  write_png=True,\
                                  color_method=method)

          filename = path_handler.skelt_circ_file(circ_bmark,
                                                  circ_indices,
                                                  circ_scale_index,
                                                  opt)
          conc_circ.write_circuit(filename)
