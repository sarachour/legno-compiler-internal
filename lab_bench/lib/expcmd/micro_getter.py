import lab_bench.lib.enums as enums
from lab_bench.lib.base_command import Command,ArduinoCommand
import math
import time
import json
import numpy as np
from lab_bench.lib.expcmd.common import *


class MicroGetStatusCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_get_status'

    @staticmethod
    def desc():
        return "[microcontroller] get chip integrator and adc status."


    @staticmethod
    def parse(args):
        return strict_do_parse("",args,MicroGetStatusCmd)

    def __repr__(self):
        return self.name()

    def execute(self,state):
        for stmt in state.analyze_chip():
            stmt.apply(state)

        print("==== overflow summary ====")
        for handle,oflow in state.statuses():
            print("%s status=%s" % (handle,oflow))
        print("=========")


class MicroGetTimeDeltaCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_get_time_delta'

    @staticmethod
    def desc():
        return "[microcontroller] get the time between samples"


    def __repr__(self):
        return self.name()

    @staticmethod
    def parse(args):
        return strict_do_parse("", args, MicroGetTimeDeltaCmd)


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.GET_TIME_BETWEEN_SAMPLES.name,
            'args':{
                'ints':[0,0,0],
            },
            'flag':False
        })


    def execute(self,state):
        resp = ArduinoCommand.execute(self,state)
        if not resp is None:
            tb_samples = resp.data(0)
            print("time_delta: %s" % tb_samples)
            state.time_between_samples_s = tb_samples
            return tb_samples


class MicroGetNumADCSamplesCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_get_num_adc_samples'

    @staticmethod
    def desc():
        return "[microcontroller] get the number of adc samples"


    def __repr__(self):
        return self.name()

    @staticmethod
    def parse(args):
        return strict_do_parse("", args, MicroGetNumADCSamplesCmd)

    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.GET_NUM_ADC_SAMPLES.name,
            'args':{
                'ints':[0,0,0],
            },
            'flag':False
        })


    def execute(self,state):
        resp = ArduinoCommand.execute(self,state)
        if not resp is None:
            n_samples = resp.data(0)
            print("n-adc=%s" % n_samples)
            state.n_adc_samples = n_samples
            return n_samples


class MicroGetNumDACSamplesCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_get_num_dac_samples'

    @staticmethod
    def desc():
        return "[microcontroller] get the number of dac samples"


    def __repr__(self):
        return self.name()


    @staticmethod
    def parse(args):
        return strict_do_parse("", args, \
                        MicroGetNumDACSamplesCmd)

    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.GET_NUM_DAC_SAMPLES.name,
            'args':{
                'ints':[0,0,0],
            },
            'flag':False
        })


    def execute(self,state):
        resp = ArduinoCommand.execute(self,state)
        if not resp is None:
            n_samples = resp.data(0)
            print("n-dac=%s" % n_samples)
            state.n_dac_samples = n_samples
            return n_samples


class MicroGetADCValuesCmd(ArduinoCommand):

    def __init__(self,adc_id,variable,filename):
        ArduinoCommand.__init__(self)
        self._filename = filename
        self._variable = variable
        self._adc_id = adc_id

    @staticmethod
    def name():
        return 'micro_get_adc_values'

    @staticmethod
    def desc():
        return "[microcontroller] get adc values."

    def __repr__(self):
        return "%s %d %s %s" % (
            self.name(),
            self._adc_id,
            self._variable,
            self._filename)

    def build_ctype(self):
        n,offset=self._args
        return build_exp_ctype({
            'type':enums.ExpCmdType.GET_ADC_VALUES.name,
            'args':{
                'ints':[self._adc_id,n,offset],
            },
            'flag':False
        })

    def execute_read_op(self,state,n,offset):
        resp = ArduinoCommand.execute(self,state)
        VAL_TO_VOLTS = 3.3
        array = resp.data(0)
        data = list(map(lambda val: val*VAL_TO_VOLTS, array))
        return data

    @staticmethod
    def parse(args):
        return strict_do_parse("{adc_id:d} {variable} {filename}", \
                               args, \
                        MicroGetADCValuesCmd)

    def execute_command(self,state):
        n = state.n_adc_samples
        buf = []
        chunksize_bytes = 1000;
        chunksize_shorts = int(chunksize_bytes/2)

        data = {}
        time = np.linspace(0,state.time_between_samples_s*n,n)
        values = np.zeros(n)
        for offset in range(0,n,chunksize_shorts):
            self._args = (n,offset)
            resp = ArduinoCommand.execute_command(self, state)
            payl = resp.data(0)
            for i,value in enumerate(payl):
                values[offset+i] = value

        obj = {
            'variable':self._variable,
            'times':list(time),
            'values':list(values)
        }
        with open(self._filename,'w') as fh:
            fh.write(json.dumps(obj,indent=4))

