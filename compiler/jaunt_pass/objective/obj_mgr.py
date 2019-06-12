import compiler.jaunt_pass.objective.phys_obj as physoptlib
import compiler.jaunt_pass.objective.basic_obj as boptlib
import compiler.jaunt_pass.objective.sweep_obj as sweepoptlib

#TODO: what is low range, high range and med range?
#TODO: setRange: integ.in, integ.out and mult have setRange functions.
#TODO: how do you set wc in the integrator? Is it through the setRange function?
class JauntObjectiveFunctionManager():

    @staticmethod
    def basic_methods():
        #return ['fast','slow','max']
        '''
        return [
            boptlib.SlowObjFunc,
            boptlib.FastObjFunc,
            boptlib.MaxSignalObjFunc,
            boptlib.MaxSignalAndSpeedObjFunc,
            boptlib.MaxSignalAndStabilityObjFunc,

        ]
        '''
        return [
            boptlib.SlowObjFunc,
            boptlib.MaxSignalAndStabilityObjFunc,
            boptlib.MaxSignalAndSpeedObjFunc
        ]

    @staticmethod
    def sweep_methods():
        return [
            sweepoptlib.MaxRandomSignalObjFunc,
            sweepoptlib.TauSweepSigObjFunc
            #physoptlib.TauSweepSNRObjFunc
        ]


    @staticmethod
    def inference_methods():
        return [
            boptlib.NoScaleFunc
        ]


    def __init__(self,jenv):
        self.method = None
        self.jenv = jenv
        self._results = {}


    @property
    def time_scaling(self):
        return self.jenv.time_scaling

    def result(self,objective):
        return self._results[objective]

    def add_result(self,objective,sln):
        self._results[objective] = sln


    def objective(self,circuit,varmap):
        assert(not self.method is None)
        gen = None
        for obj in self.basic_methods() +self.inference_methods() + self.sweep_methods():
            if obj.name() == self.method:
                gen = obj.make(circuit,self,varmap)

        for obj in gen:
            yield obj
