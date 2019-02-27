import tinydb as tdb
import os
from enum import Enum

class ExperimentPathHandler:
    def __init__(self,name):
        self.set_root_dir(name)
        if not os.path.exists(self.ROOT_DIR):
            os.makedirs(self.ROOT_DIR)

        if not os.path.exists(self.TIME_DIR):
            os.makedirs(self.TIME_DIR)

        if not os.path.exists(self.FREQ_DIR):
            os.makedirs(self.FREQ_DIR)

        if not os.path.exists(self.SCRIPT_DIR):
            os.makedirs(self.SCRIPT_DIR)

        if not os.path.exists(self.PLOT_DIR):
            os.makedirs(self.PLOT_DIR)

        if not os.path.exists(self.MODEL_DIR):
            os.makedirs(self.MODEL_DIR)

        self._name = name

    def set_root_dir(self,name):
        self.ROOT_DIR = "outputs/moira/%s" % name
        self.SCRIPT_DIR = self.ROOT_DIR + "/scripts"
        self.TIME_DIR = self.ROOT_DIR + "/time"
        self.FREQ_DIR = self.ROOT_DIR + "/freq"
        self.PLOT_DIR = self.ROOT_DIR + "/plot"
        self.MODEL_DIR = self.ROOT_DIR + "/model"



    def script_file(self,ident,trial):
        return self.SCRIPT_DIR+ "/%s_%s.grendel" % (ident,trial)

    def timeseries_file(self,ident,trial):
        return self.TIME_DIR+ "/%s_%s.json" % (ident,trial)


    def time_xform_file(self,ident,trial):
        return self.MODEL_DIR+ "/xf_time_%s_%s.json" % (ident,trial)

    def signal_xform_file(self,ident,trial):
        return self.MODEL_DIR+ "/xf_sig_%s_%s.json" % (ident,trial)

    def noise_file(self,ident,trial):
        return self.MODEL_DIR + "/noise_%s_%s.json" % (ident,trial)

    def freq_file(self,ident,trial):
        return self.FREQ_DIR+ "/freq_%s_%s.json" % (ident,trial)

    def plot_file(self,ident,trial,tag):
        return self.PLOT_DIR+ "/%s_%s_%s.png" % (ident,trial,tag)

    def model_graph(self,round_no,tag):
        return self.MODEL_DIR+ "/%s_model_%s_%s.png" % (self._name,round_no,tag)


    def model_file(self,round_no):
        return self.MODEL_DIR+ "/%s_model_%s.json" % (self._name,round_no)

    def has_file(self,filepath):
        return os.path.exists(filepath)

    def database_file(self,name):
        return self.ROOT_DIR+"/%s.json" % name

class ExperimentDB:
    class Status(Enum):
        PENDING = "pending",
        RAN = "ran"
        ALIGNED = "aligned"
        XFORMED = "xformed"
        FFTED = "ffted"
        DENOISED = "denoised"


    def __init__(self,name):
        self._name = name
        self.paths = ExperimentPathHandler(name)
        path = self.paths.database_file(name)
        self._db = tdb.TinyDB(path)
        self._update()

    def to_ident(self,inputs,output,round_no,num_periods):
        strep=self._name
        strep+="_".join(inputs)
        strep+=".%s" % output
        strep+="[%d]" % round_no
        strep+="[%d]" % num_periods
        hashval= hash(strep)
        if hashval < 0:
            return "n"+hex(abs(hashval)).split('x')[1]
        else:
            return "p"+hex(abs(hashval)).split('x')[1]

    def insert(self,round_no,inputs,output,period,num_periods=1,trials=1,model=None):
        ident = self.to_ident(inputs,output,round_no,num_periods)
        q = tdb.Query()
        prev_exps = self._db.search(q.ident == ident)
        start_trial = 0
        for exp in prev_exps:
            start_trial = max(start_trial,exp['trial'])

        for trial_id in range(start_trial+1,start_trial+trials+1):
            datum = {
                'trial': trial_id,
                'ident': ident,
                'inputs': inputs,
                'status': ExperimentDB.Status.PENDING.name,
                'output': output,
                'period': period,
                'num_periods': num_periods,
                'model_id': model,
                'round': round_no
            }
            self._db.insert(datum)

    def is_empty(self):
        return len(self._db.all()) == 0

    def rounds(self):
        if self.is_empty():
            return None

        return set(map(lambda d: d['round'],self._db.all()))


    def last_round(self):
        if self.is_empty():
            return None

        return max(map(lambda d: d['round'],self._db.all()))

    def _update(self):
        updates = []
        for result in self._db.all():
            ident,trial = result['ident'],result['trial']
            has_signal_xform_file = self.paths.has_file(\
                self.paths.signal_xform_file(ident,trial))
            has_time_xform_file = self.paths.has_file(\
                self.paths.time_xform_file(ident,trial))
            has_noise_file = self.paths.has_file(\
                self.paths.noise_file(ident,trial))
            has_freq_file = self.paths.has_file(\
                self.paths.freq_file(ident,trial))

            has_timeseries_file = self.paths.has_file(\
                self.paths.timeseries_file(ident,trial))

            if not has_timeseries_file:
                updates.append((ident,trial,ExperimentDB.Status.PENDING))
            elif not has_time_xform_file:
                updates.append((ident,trial,ExperimentDB.Status.RAN))

            elif not has_signal_xform_file:
                updates.append((ident,trial,ExperimentDB.Status.ALIGNED))
            elif not has_freq_file:
                updates.append((ident,trial,ExperimentDB.Status.XFORMED))
            elif not has_noise_file:
                updates.append((ident,trial,ExperimentDB.Status.FFTED))

        for ident,trial,status in updates:
            self.set_status(ident,trial,status)

    def all(self):
        for result in self._db.all():
            yield result['ident'],result['trial'],result['status'],result['round'], \
                result['period'],result['num_periods'],result['inputs'], \
                result['output'],result['model_id']


    def get_by_status(self,status):
        q = tdb.Query()
        results = self._db.search(q.status == status.name)
        trials = {}
        args = {}
        for result in results:
            if not result['ident'] in trials:
                trials[result['ident']] = []

            assert(result['status'] == status.name)
            trials[result['ident']].append(result['trial'])
            args[result['ident']] = (result['period'],\
                                     result['num_periods'],\
                                     result['inputs'], \
                                     result['output'], \
                                     result['model_id'],
                                     result['round'])

        keys = list(args.keys())
        keys.sort()
        for ident in keys:
            period,num_periods,inputs,outputs,model_id,round_id = args[ident]
            yield ident,trials[ident],round_id,\
                period,num_periods,inputs,outputs,model_id

    def set_status(self,ident,trial,status):
        q = tdb.Query()
        q = tdb.Query()
        results = self._db.search( \
                                  (q.ident == ident) & \
                                  (q.trial == trial))
        assert(len(results) == 1)
        self._db.update({'status':status.name}, \
                        (q.ident == ident) & \
                        (q.trial == trial))



    def __repr__(self):
        st = ""
        for row in self._db.all():
            args = map(lambda tup: "%s:%s" % tup,
                               row.items())
            st+="\t".join(args)
            st+="\n"

        return st
