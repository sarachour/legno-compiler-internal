from moira.db import ExperimentDB

# script
class ScriptGenerator:

    def __init__(self):
        self._rels = {}
        self._iface = {}
        self._prog = {'preamble':{},'config':{},'getter':{}}

    def bind_iface(self,idx,iface):
        self._iface[idx] = (iface)

    def set_getter(self,idx,getter):
        self._prog['getter'][idx] = getter

    def set_config(self,idx,config):
        self._prog['config'][idx] = config

    def set_preamble(self,idx,preamble):
        self._prog['preamble'][idx] = preamble

    def default_preamble(self):
        return lambda sim_time: ['reset',
                                 'micro_use_due_dac 0',
                                 'osc_set_volt_range 0 -1.5 2.5',
                                 'osc_set_volt_range 1 -1.5 2.5',
                                 'osc_set_sim_time %f' % sim_time
                                 'micro_set_sim_time %f %f' % (sim_time,sim_time),
                                 'micro_compute_offsets',
                                 'micro_get_num_adc_samples',
                                 'micro_get_num_dac_samples',
                                 'micro_get_time_delta',
                                 'micro_use_chip',
                                 'osc_setup_trigger'
                              ]

    def default_posthook(self):
        return lambda : [
            'micro_get_overflows',
            'micro_teardown_chip'
        ]

    def generate(self,sim_time,input_period,ins,out,paths):
        prog = []
        def q(stmt):
            prog.append(stmt)

        q('reset')
        q('micro_set_sim_time %f %f' % (sim_time,input_period))
        q('get_num_adc_samples')
        q('get_num_dac_samples')
        q('get_time_between_samples')
        q('use_osc')
        if out in self._prog['preamble']:
            preamble = self._prog['preamble'][out]
        else:
            preamble = self.default_preamble()

        getter = self._prog['getter'][out]
        config = self._prog['config'][out] \
               if out in self._prog['config'] else None

        for stmt in preamble(sim_time):
            q(stmt)

        for inp,iface_fn in self._iface.items():
            q(iface_fn(ins[inp]))

        if not config is None:
            for stmt in config:
                q(stmt)

        for idx,path in enumerate(paths):
            # run experiment
            q('run')
            q(getter(path))
            if idx == len(paths) - 1:
                for stmt in self.default_posthook():
                    q(stmt)

            yield prog
            prog = []

        return prog

class AnalyticalModel:

    def __init__(self,name,n_ins,n_outs):
        self.name = name
        self._ins = dict(map(lambda i: (i,"inp%d" % i),
                             range(0,n_ins)))
        self._outs = dict(map(lambda i: (i,"out%d" % i),
                              range(0,n_outs)))

        self.scriptgen = ScriptGenerator()
        self.db = ExperimentDB(self.name)
        self.n_inputs = n_ins
        self.n_outputs = n_outs

class AnalyticalModelManager:

    def __init__(self):
        self._models = {}


    def get(self,name):
        return self._models[name]

    def register(self,model):
        self._models[model.name] = model

def build_manager():
    mgr = AnalyticalModelManager()

    am = AnalyticalModel('adc0',1,1)
    am.scriptgen.bind_iface(0,lambda f: "set_due_dac_values 0 %s" % f)
    am.scriptgen.set_config(0,
                       ['mkconn chip_input 0 3 2 chip_output 0 3 2'])
    am.scriptgen.set_getter(0,
                            lambda args: 'get_osc_values differential 0 1 %s %s' \
                            % (args[0],args[1]))
    mgr.register(am)

    '''
    am = AnalyticalModel('adc0',1,1)
    am.scriptgen.bind_expr(0,'inp0*0.6534')
    am.scriptgen.bind_iface(0,lambda f: "set_due_dac_values 0 %s" % f)
    am.scriptgen.set_preamble(0,
                       ['use_due_dac 0', 'use_osc',
                        'set_volt_ranges differential 0.2 1.2 0.2 1.2'])
    am.scriptgen.set_config(0,
                       ['mkconn chip_input 0 3 2 chip_output 0 3 2'])
    am.scriptgen.set_getter(0,
                       lambda name: 'get_osc_values differential %s' % name)
    mgr.register(am)


    am = AnalyticalModel('adc1',1,1)
    am.scriptgen.bind_expr(0,'inp1*0.6534')
    am.scriptgen.bind_iface(0,lambda f: "set_due_dac_values 1 %s" % f)
    am.scriptgen.set_preamble(0,
                       ['use_due_dac 1', 'use_osc',
                        'set_volt_ranges differential 0.2 1.2 0.2 1.2'])
    am.scriptgen.set_config(0,
                       ['mkconn chip_input 0 3 3 chip_output 0 3 3'])
    am.scriptgen.set_getter(0,
                       lambda name: 'get_osc_values differential %s' % name)
    mgr.register(am)

    # due DAC than VDIV
    ref = "inp%d*0.030"
    am = AnalyticalModel('vdiv1',1,1)
    am.scriptgen.bind_expr(0,ref % 1)
    am.scriptgen.bind_iface(0,lambda f: "set_due_dac_values 1 %s" % f)
    am.scriptgen.set_preamble(0,
                       ['use_due_dac 1', 'use_osc',
                        'set_volt_ranges differential 0.0 0.080 0.0 0.080'])
    am.scriptgen.set_getter(0, \
                            lambda name: 'get_osc_values differential %s' % name)
    mgr.register(am)



    am = AnalyticalModel('vdiv0',1,1)
    am.scriptgen.bind_expr(0,ref % 0)
    am.scriptgen.bind_iface(0,lambda f: "set_due_dac_values 0 %s" % f)
    am.scriptgen.set_preamble(0,
                       ['use_due_dac 0', 'use_osc',
                        'set_volt_ranges differential 0.0 0.080 0.0 0.080'])
    am.scriptgen.set_getter(0,
                       lambda name: 'get_osc_values differential %s' % name)
    mgr.register(am)

    am = AnalyticalModel('due_dac0',1,1)
    am.scriptgen.bind_expr(0,'inp0*1.1 + 1.65')
    am.scriptgen.bind_iface(0,lambda f: "set_due_dac_values 0 %s" % f)
    am.scriptgen.set_preamble(0,
                       ['use_due_dac 0', 'use_osc',
                       'set_volt_ranges direct 0.55 2.75'])
    am.scriptgen.set_getter(0,
                       lambda name: 'get_osc_values direct %s' % name)
    mgr.register(am)
    '''

    return mgr
