import lab_bench.lib.enums as enums
import lab_bench.lib.cstructs as cstructs
import lab_bench.lib.infer.bayes as bayes
from lab_bench.lib.base_command import Command,AnalogChipCommand
from lab_bench.lib.chipcmd.data import CircLoc
from lab_bench.lib.chipcmd.common import *
import lab_bench.lib.chipcmd.state as chipstate
import json
import struct
import os
import matplotlib.pyplot as plt
from matplotlib import gridspec
from bayes_opt import UtilityFunction

def posterior(optimizer, x_obs, y_obs, grid):
    optimizer._gp.fit(x_obs, y_obs)

    mu, sigma = optimizer._gp.predict(grid, return_std=True)
    return mu, sigma

def plot_gp(optimizer, x):
    fig = plt.figure(figsize=(16, 10))
    steps = len(optimizer.space)
    fig.suptitle(
        'Gaussian Process and Utility Function After {} Steps'.format(steps),
        fontdict={'size':30}
    )
    gs = gridspec.GridSpec(2, 1, height_ratios=[3, 1]) 
    axis = plt.subplot(gs[0])
    acq = plt.subplot(gs[1])
    x_obs = np.array([[res["params"]["x0"]] for res in optimizer.res])
    y_obs = np.array([res["target"] for res in optimizer.res])
    mu, sigma = posterior(optimizer, x_obs, y_obs, x)
    #axis.plot(x, y, linewidth=3, label='Target')
    axis.plot(x_obs.flatten(), y_obs, 'D', markersize=8, label=u'Observations', color='r')
    axis.plot(x, mu, '--', color='k', label='Prediction')

    axis.fill(np.concatenate([x, x[::-1]]), 
              np.concatenate([mu - 1.9600 * sigma, (mu + 1.9600 * sigma)[::-1]]),
        alpha=.6, fc='c', ec='None', label='95% confidence interval')
    axis.set_xlim((-2, 10))
    axis.set_ylim((None, None))
    axis.set_ylabel('f(x)', fontdict={'size':20})
    axis.set_xlabel('x', fontdict={'size':20})
    utility_function = UtilityFunction(kind="ucb", kappa=5, xi=0)
    utility = utility_function.utility(x, optimizer._gp, 0)
    acq.plot(x, utility, label='Utility Function', color='purple')
    acq.plot(x[np.argmax(utility)], np.max(utility), '*', markersize=15, 
             label=u'Next Best Guess', markerfacecolor='gold', markeredgecolor='k', markeredgewidth=1)
    acq.set_xlim((-2, 10))
    acq.set_ylim((0, np.max(utility) + 0.5))
    acq.set_ylabel('Utility', fontdict={'size':20})
    acq.set_xlabel('x', fontdict={'size':20})
    axis.legend(loc=2, bbox_to_anchor=(1.01, 1), borderaxespad=0.)
    acq.legend(loc=2, bbox_to_anchor=(1.01, 1), borderaxespad=0.)
    plt.savefig("fit.png")


class ExecuteInput(AnalogChipCommand):

    def __init__(self,blk,chip,tile,slce, \
                 inputs, \
                 index=None, \
                 mode=0):
        AnalogChipCommand.__init__(self)
        self._blk = enums.BlockType(blk)
        self._loc = CircLoc(chip,tile,slce,index=0 if index is None \
                            else index)
        self._inputs = inputs
        self._mode = mode
        self.test_loc(self._blk, self._loc)

    def build_ctype(self):
        loc_type = self._loc.build_ctype()
        print(loc_type)
        return build_circ_ctype({
            'type':enums.CircCmdType.CHARACTERIZE.name,
            'data':{
                'prof':{
                  'blk': self._blk.code(),
                  'loc': loc_type,
                  'in0': self._inputs[0],
                  'in1': self._inputs[1] if len(self._inputs) > 1 else 0.0,
                  'mode': self._mode
                }
            }
        })

    def execute_command(self,env):
      resp = ArduinoCommand.execute_command(self,env)
      state_size = int(resp.data(0)[0])
      result_size = int(resp.data(0)[1])
      base = 2
      state_data = bytes(resp.data(0)[base:(base+state_size)])
      result_data = bytes(resp.data(0)[(base+state_size):])
      st = chipstate.BlockState \
                    .toplevel_from_cstruct(self._blk,
                                           self._loc,
                                           state_data,
                                           targeted=False)
      result = cstructs.profile_t() \
                       .parse(result_data);
      bias = from_float16(result.bias)
      noise = from_float16(result.noise)
      out = from_float16(result.output)
      in0 = from_float16(result.input0)
      in1 = from_float16(result.input1)
      port = enums.PortName.from_code(result.port)
      return {
        'bias':bias,
        'noise':noise,
        'out':out,
        'in0':in0,
        'in1':in1,
        'port':port
      }

class ProfileCmd(Command):

    def __init__(self,blk,chip,tile,slce,index=None):
        AnalogChipCommand.__init__(self)
        self._blk = enums.BlockType(blk)
        self._loc = CircLoc(chip,tile,slce,index=0 if index is None \
                            else index)
        if self._blk == enums.BlockType.MULT:
          self._n_inputs = 2
        else:
          self._n_inputs = 1

    @staticmethod
    def name():
        return 'profile'

    def get_output(self,state,inputs,mode=0):
      cmd = ExecuteInput(self._blk, \
                         self._loc.chip, \
                         self._loc.tile, \
                         self._loc.slice, \
                         inputs=inputs, mode=mode)
      return cmd.execute(state)

    def update_database(self,state,profile):
        entry = env.state_db.get(st.key)
        env.state_db.put(st,entry.targeted,
                         profile=profile + entry.profile,
                         success=entry.success,
                         max_error=entry.tolerance)

    def insert_result(self,env,resp):
        title = "profiled %s.%s " % (self._blk,self._loc)
        send_mail(title,log)
        return True


    def execute_command(self,state):
      def unknown_fxn(x0,y):
          prop = "bias"
          row = self.get_output(state,[x0],
                                mode=0)
          return -(row[prop]-y)**2


      opt = bayes.make_optimizer(self._n_inputs, \
                                 unknown_fxn)
      nsteps = 10
      x = np.linspace(-1, 1, 100).reshape(-1, 1)
      for _ in range(0,nsteps):
        opt.maximize(
            init_points=0,
            n_iter=1
        )
        plot_gp(opt, x)
        input()

      for i, res in enumerate(opt.res):
          print("Iteration {}: \n\t{}".format(i, res))

      input("stop")

    @staticmethod
    def parse(args):
        result = parse_pattern_block_loc(args,ProfileCmd.name(),
                                         targeted=True)
        if result.success:
            data = result.value
            return CharacterizeCmd(data['blk'],
                                   data['chip'],
                                   data['tile'],
                                   data['slice'],
                                   data['index'],
                                   targeted=data['targeted'])

        else:
            print(result.message)
            raise Exception("<parse_failure>: %s" % args)



