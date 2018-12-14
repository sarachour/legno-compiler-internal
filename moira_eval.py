from moira.lib.blackbox import BlackBoxModel
import moira.model as modellib
import sys
import argparse
from moira.db import ExperimentDB
import lab_bench.analysis.det_xform as dx

def eval_experiment(model,blackbox,model_id,round_no,ident,trial):
  print(model_id,round_no)
  if round_no is None or  model_id >= round_no:
    print("[%s:%s] [TRAIN]" % (ident,trial))
  else:
    print("[%s:%s] [TEST]" % (ident,trial))

  xformfile = model.db.paths.time_xform_file(ident,trial)
  meas_delay = dx.DetTimeXform.read(xformfile).delay
  print('%s \in %s' % (meas_delay,blackbox.time_model.delay))
  prob = blackbox.time_model.delay.pdf(meas_delay)
  print("delay prob: %e" % prob)

def evaluate(model,blackbox,model_id):
  for ident,trials,round_no,period,n_cycles,inputs,output,_ in \
      model.db.get_by_status(ExperimentDB.Status.DENOISED):
    for trial in trials:
      eval_experiment(model,blackbox,model_id,round_no,ident,trial)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, \
                          help='component model to evaluate.')
    parser.add_argument('--model-id', type=int, \
                          help='model id to evaluate.')

    args = parser.parse_args()
    mgr = modellib.build_manager()
    model = mgr.get(args.name)
    print(model.db)
    model_file = model.db.paths.model_file(args.model_id)
    black_box = BlackBoxModel.read(model_file)
    evaluate(model,black_box,args.model_id)

main()
