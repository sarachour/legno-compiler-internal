from moira.db import ExperimentDB

# script
class ScriptGenerator:

    def __init__(self):
        self._rels = {}
        self._iface = {}
        self._prog = {}

    def bind_expr(self,idx,expr):
        self._rels[idx] = expr

    def bind_iface(self,idx,iface):
        self._iface[idx] = (iface)

    def set_prog(self,idx,preamble,getter):
        self._prog[idx] = (preamble,getter)

    def generate(self,sim_time,ins,out,paths):
        prog = []
        def q(stmt):
            prog.append(stmt)

        q('reset')
        q('set_ref_func %s' % self._rels[out])
        q('set_sim_time %f' % sim_time)
        q('get_num_samples')
        q('get_time_between_samples')
        q('use_osc')
        preamble,getter = self._prog[out]
        prog += preamble
        q('compute_offsets')
        for inp,iface_fn in self._iface.items():
            q(iface_fn(ins[inp]))

        for path in paths:
            q('run')
            q(getter(path))
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
    am = AnalyticalModel('vdiv0',1,1)
    am.scriptgen.bind_expr(0,'inp0*0.030')
    am.scriptgen.bind_iface(0,lambda f: "set_due_dac_values 0 %s" % f)
    am.scriptgen.set_prog(0,
                       ['use_due_dac 0', 'use_osc',
                        'set_volt_ranges differential 0.0 0.080 0.0 0.080'],
                       lambda name: 'get_osc_values differential %s' % name)
    mgr.register(am)

    am = AnalyticalModel('due_dac0',1,1)
    am.scriptgen.bind_expr(0,'inp0*1.1 + 1.65')
    am.scriptgen.bind_iface(0,lambda f: "set_due_dac_values 0 %s" % f)
    am.scriptgen.set_prog(0,
                       ['use_due_dac 0', 'use_osc',
                        'set_volt_ranges direct 0.55 2.75'],
                       lambda name: 'get_osc_values direct %s' % name)
    mgr.register(am)

    return mgr
