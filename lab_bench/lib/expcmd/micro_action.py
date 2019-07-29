import lab_bench.lib.enums as enums
import lab_bench.lib.util as util
from lab_bench.lib.base_command import Command,ArduinoCommand
from lab_bench.lib.expcmd.common import *
import lab_bench.lib.util as util
import math
import time
import json
import numpy as np
import construct

class MicroResetCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_reset'

    @staticmethod
    def desc():
        return "[microcontroller] reset any set flags, values and buffers on the microcontroller."

    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.RESET.name,
            'args':{
                'ints':[0,0,0],
            },
            'flag':False
        })


    def execute(self,state):
        state.reset()
        ArduinoCommand.execute(self,state)


    @staticmethod
    def parse(args):
        return strict_do_parse("", args, MicroResetCmd)

    def __repr__(self):
        return self.name()


class MicroUseArdADCCmd(ArduinoCommand):
    def __init__(self,adc_no):
        ArduinoCommand.__init__(self)
        self._adc_id = adc_no

    @staticmethod
    def name():
        return "micro_use_ard_adc"

    @staticmethod
    def desc():
        return "[microcontroller] use the arduino's analog to digital converter."

    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_ADC.name,
            'args':{
                'ints':[self._adc_id,0,0],
            },
            'flag':False
        })


    @staticmethod
    def parse(args):
        return strict_do_parse("{adc_no:d}", args, MicroUseArdADCCmd)

    def execute(self,state):
        state.use_adc(self._adc_id)
        ArduinoCommand.execute(self,state)

    def __repr__(self):
        return "%s %d" % (self.name(), self._adc_id)


class MicroUseArdDACCmd(ArduinoCommand):

    def __init__(self,dac_id,periodic):
        ArduinoCommand.__init__(self)
        self._dac_id = dac_id
        self._periodic = bool(periodic)


    @staticmethod
    def name():
        return 'micro_use_ard_dac'

    @staticmethod
    def desc():
        return "use the arduino's digital to analog converter (time varying signal)."


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_DAC.name,
            'args':{
                'ints':[self._dac_id,0,0],
            },
            'flag':self._periodic
        })


    def execute(self,state):
        state.use_dac(self._dac_id)
        return ArduinoCommand.execute(self,state)


    @staticmethod
    def parse(args):
        return strict_do_parse("{dac_id:d} {periodic}", args, \
                        MicroUseArdDACCmd)

    def __repr__(self):
        return "%s %d %s" % (self.name(),self._dac_id, \
                             str(self._periodic))



class MicroSetDACValuesCmd(ArduinoCommand):

    def __init__(self,dac_id,expr,scf,time_scf):
        ArduinoCommand.__init__(self)
        self.dac_id = dac_id
        self.time_scf = time_scf
        self.scf = scf
        self.expr = expr

    @staticmethod
    def name():
        return 'micro_set_dac_values'


    @staticmethod
    def desc():
        return "[microconotroller] set the dac values to an expression." + \
            "tau=time constant, scf=scaling factor for input, "+\
            "periodic=is this input periodic."

    @staticmethod
    def parse(args):
        return strict_do_parse("{dac_id:d} {expr} {time_scf:g} {scf:g}", \
                        args, \
                        MicroSetDACValuesCmd)


    def build_ctype(self,offset=None,n=None):
        return build_exp_ctype({
            'type':enums.ExpCmdType.SET_DAC_VALUES.name,
            'args':{
                'ints':[self.dac_id,n,offset],
            },
            'flag': False
        })

    def build_dtype(self,buf):
        return construct.Array(len(buf),
                        construct.Float32l)

    def compute_value(self,state,idx):
        delta = state.time_between_samples_s
        args = {'t_':idx*delta*self.time_scf,\
                'i_':idx}
        value = self.scf*util.eval_func(self.expr,args)
        return args['t_'],value

    def execute(self,state):
        if state.dummy:
            return

        n = state.n_dac_samples
        buf = []
        for idx in range(0,n):
            _,value = self.compute_value(state,idx)
            buf.append(value)

        ArduinoCommand.execute(self,state,
                               {'raw_data':buf, \
                                'n_data_bytes':250,
                                'elem_size':4})


    def __repr__(self):
        return "%s %d %s %f %f" % \
            (self.name(),self.dac_id,self.expr,
             self.scf,self.time_scf)




class MicroSetSimTimeCmd(ArduinoCommand):

    def __init__(self,sim_time,input_time,frame_time=None):
        ArduinoCommand.__init__(self)
        if(sim_time <= 0):
            self.fail("invalid simulation time: %s" % sim_time)

        self._sim_time = sim_time
        self._input_time = input_time
        self._frame_time = (sim_time if frame_time is None else frame_time)


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.SET_SIM_TIME.name,
            'args':{
                'floats':[self._sim_time,
                          self._input_time,
                          self._frame_time]
            },
            'flag':False
        })


    @staticmethod
    def name():
        return 'micro_set_sim_time'

    def __repr__(self):
        return "%s %.3e %.3e" % (self.name(),self._sim_time,self._input_time)


    @staticmethod
    def parse(args):
        return strict_do_parse("{sim_time:g} {input_time:g}", args, \
                               MicroSetSimTimeCmd)


    def execute(self,state):
        state.sim_time = self._sim_time
        state.input_time = self._input_time
        ArduinoCommand.execute(self,state)



    @staticmethod
    def desc():
        return "[microcontroller] set the simulation time and input time"


class MicroComputeOffsetsCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_compute_offsets'

    @staticmethod
    def desc():
        return "compute the offsets for the data buffer. Must be completed before writing data to dacs/execution."


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.COMPUTE_OFFSETS.name,
            'args':{
                'ints':[0,0,0],
            },
            'flag':False
        })


    def execute(self,state):
        ArduinoCommand.execute(self,state)

    @staticmethod
    def parse(args):
        return strict_do_parse("",args,MicroComputeOffsetsCmd)

    def __repr__(self):
        return self.name()


class MicroUseAnalogChipCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_use_chip'

    @staticmethod
    def desc():
        return "mark the analog chip as used."


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_ANALOG_CHIP.name,
            'args':{
                'ints':[0,0,0],
            },
            'flag':False
        })


    def execute(self,state):
        state.use_analog_chip = True
        ArduinoCommand.execute(self,state)

    @staticmethod
    def parse(args):
        return strict_do_parse("",args,MicroUseAnalogChipCmd)

    def __repr__(self):
        return self.name()


class MicroUseOscCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_use_osc'

    @staticmethod
    def desc():
        return "[microcontroller] setup trigger on pin 23 for oscilloscope."



    @staticmethod
    def parse(args):
        return strict_do_parse("",args,MicroUseOscCmd)


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_OSC.name,
            'args':{
                'ints':[0,0,0],
            },
            'flag':False
        })



    def execute(self,state):
        state.use_osc = True
        ArduinoCommand.execute(self,state)

    def __repr__(self):
        return self.name()


class MicroRunCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_run'

    @staticmethod
    def desc():
        return "[microcontroller] run the experiment."


    @staticmethod
    def parse(args):
        return strict_do_parse("",args,MicroRunCmd)


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.RUN.name,
            'args':{
                'ints':[0,0,0],
            },
            'flag':False
        })


    def execute(self,state):
        resp = ArduinoCommand.execute(self,state)

    def __repr__(self):
        return self.name()

