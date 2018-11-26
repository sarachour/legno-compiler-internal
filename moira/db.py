import tinydb as tdb
import os
from enum import Enum

class ExperimentDB:
    class Status(Enum):
        PENDING = "pending",
        RAN = "ran"
        ALIGNED = "aligned"
        USED = "used"


    ROOT_DIR = "outputs/grendel"
    SCRIPT_DIR = ROOT_DIR + "/scripts"
    TIME_DIR = ROOT_DIR + "/time"
    FREQ_DIR = ROOT_DIR + "/freq"
    PLOT_DIR = ROOT_DIR + "/plot"
    MODEL_DIR = ROOT_DIR + "/model"

    def __init__(self,name):
        if not os.path.exists(ExperimentDB.ROOT_DIR):
            os.makedirs(ExperimentDB.ROOT_DIR)

        if not os.path.exists(ExperimentDB.TIME_DIR):
            os.makedirs(ExperimentDB.TIME_DIR)

        if not os.path.exists(ExperimentDB.FREQ_DIR):
            os.makedirs(ExperimentDB.FREQ_DIR)

        if not os.path.exists(ExperimentDB.SCRIPT_DIR):
            os.makedirs(ExperimentDB.SCRIPT_DIR)

        if not os.path.exists(ExperimentDB.PLOT_DIR):
            os.makedirs(ExperimentDB.PLOT_DIR)

        if not os.path.exists(ExperimentDB.PLOT_DIR):
            os.makedirs(ExperimentDB.PLOT_DIR)

        path = ExperimentDB.ROOT_DIR+"/%s.json" % name
        self._db = tdb.TinyDB(path)
        self._name = name

    def to_ident(self,inputs,output):
        strep=self._name
        strep+="_".join(inputs)
        strep+=".%s" % output
        hashval= hash(strep)
        if hashval < 0:
            return "n"+hex(abs(hashval)).split('x')[1]
        else:
            return "p"+hex(abs(hashval)).split('x')[1]

    def insert(self,round_no,inputs,output,trials,model=None):
        ident = self.to_ident(inputs,output)
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
                'round': round_no
            }
            self._db.insert(datum)

    def is_empty(self):
        return len(self._db.all()) == 0

    def last_round(self):
        return max(map(lambda d: d['round'],self._db.all()))

    def get_by_status(self,status):
        q = tdb.Query()
        results = self._db.search(q.status == status.name)
        trials = {}
        args = {}
        for result in results:
            if not result['ident'] in trials:
                trials[result['ident']] = []

            trials[result['ident']].append(result['trial'])
            args[result['ident']] = (result['inputs'],result['output'])

        for ident,(inputs,outputs) in args.items():
            yield ident,trials[ident],inputs,outputs

    def set_status(self,ident,trial,status):
        q = tdb.Query()
        self._db.update({'status':status.name},
                  q.ident == ident and q.trial == trial)

    def script_file(self,ident):
        return ExperimentDB.SCRIPT_DIR+ "/%s.grendel" % (ident)


    def timeseries_file(self,ident,trial):
        return ExperimentDB.TIME_DIR+ "/%s_%s.json" % (ident,trial)


    def freq_file(self,ident,trial):
        return ExperimentDB.FREQ_DIR+ "/%s_%s.json" % (ident,trial)

    def plot_file(self,ident,trial,tag):
        return ExperimentDB.PLOT_DIR+ "/%s_%s_%s.png" % (ident,trial,tag)

    def model_file(self,round_no):
        return ExperimentDB.MODEL_DIR+ "/model_%s.json" % (round_no)



