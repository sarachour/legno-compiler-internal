import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
import lib.util as util
from lib.base_command import Command,ArduinoCommand,OptionalValue
import math
import construct
import matplotlib.pyplot as plt
import devices.sigilent_osc as osclib
import time
import json
import numpy as np
import analysis.waveform as waveform

def build_exp_ctype(exp_data):
    return {
        'test':ArduinoCommand.DEBUG,
        'type':enums.CmdType.EXPERIMENT_CMD.name,
        'data': {
            'exp_cmd':exp_data
        }
    }

def do_parse(cmd,args,ctor):
    line = " ".join(args)
    if cmd == "" or cmd is None:
        full_cmd = ctor.name()
    else:
        full_cmd = " ".join([ctor.name(),cmd])
    result = parselib.parse(full_cmd,line)
    if result is None:
        return OptionalValue.error("usage:[%s]\nline:[%s]" % (full_cmd,line))

    obj = ctor(**result.named)
    return OptionalValue.value(obj)

def strict_do_parse(cmd,args,ctor):
    result = do_parse(cmd,args,ctor)
    if result.success:
        return result.value

    raise Exception(result.message)


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
        build_exp_ctype({
            'type':enums.ExpCmdType.GET_ADC_VALUES.name,
            'args':{
                'ints':[self._adc_id,n,offset],
            },
            'flag':False
        })

    def execute_read_op(self,state,n,offset):
        self._args = (n,offset)
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
            datum = self.execute_read_op(state,
                                         chunksize_shorts,
                                         offset)
            for i,value in enumerate(datum):
                values[offset+i] = value

        obj = {
            'variable':self._variable,
            'times':list(time),
            'values':list(values)
        }
        with open(self._filename,'w') as fh:
            fh.write(json.dumps(obj,indent=4))


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
        args = {'t':idx*delta*self.time_scf,\
                'i':idx}
        value = self.scf*util.eval_func(self.expr,args)
        return args['t'],value

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


class OscSetVoltageRangeCmd(Command):

    def __init__(self,chan_id,low,high):
        Command.__init__(self)
        self._chan_id = chan_id
        self._low = low
        self._high = high

    @staticmethod
    def name():
        return 'osc_set_volt_range'


    @staticmethod
    def desc():
        return "[oscilloscope] set the ranges of the voltages read from the oscilloscope."


    def __repr__(self):
        return "%s %d %f %f" % (self.name(),self._chan_id,
                                self._low,self._high)


    @staticmethod
    def parse(args):
        return strict_do_parse("{chan_id:d} {low:g} {high:g}", \
                        args, \
                        OscSetVoltageRangeCmd)


    def execute(self,state):
        if state.dummy:
            return

        vdivs = state.oscilloscope.VALUE_DIVISIONS
        chan = state.oscilloscope.analog_channel(self._chan_id)
        volt_offset = -(self._low+self._high)/2.0
        volts_per_div = (self._high- self._low)/vdivs
        state.oscilloscope \
            .set_voltage_offset(chan,volt_offset)
        state.oscilloscope \
             .set_volts_per_division(chan,volts_per_div)


class OscGetValuesCmd(Command):

    def __init__(self,filename,variable,chan_low,chan_high=None):
        Command.__init__(self)
        self._filename = filename
        self._differential = False if chan_high is None else True
        self._chan_low = chan_low
        self._chan_high = chan_high
        self._variable = variable

    @staticmethod
    def name():
        return 'osc_get_values'


    @staticmethod
    def desc():
        return "[oscilloscope] get the values read from an oscilloscope."


    @staticmethod
    def parse(args):
        line = " ".join(args)
        types = ['differential','direct']
        cmd1 = "differential {chan_low:d} {chan_high:d} {variable} {filename}"
        opt_result1 = do_parse(cmd1, args, OscGetValuesCmd)
        if opt_result1.success:
            return opt_result1.value

        cmd2 = "direct {chan_low:d} {variable} {filename}"
        opt_result2 = do_parse(cmd2,args,OscGetValuesCmd)
        if opt_result2.success:
            return opt_result2.value

        raise Exception(opt_result1.message + "\nOR\n" +
                        opt_result2.message)

    def process_data(self,state,filename,variable,chan1,chan2):
        # compute differential or direct
        if self._differential:
            out_t1,out_v1 = chan1
            out_t2,out_v2 = chan2
            out_v = list(np.subtract(out_v1,out_v2))
            assert(all(np.equal(out_t1,out_t2)))
            out_t = out_t1

        else:
            out_t,out_v = chan1

        theo_time_per_div = float(state.sim_time) / state.oscilloscope.TIME_DIVISIONS
        act_time_per_div = state.oscilloscope\
                                .closest_seconds_per_division(theo_time_per_div)
        # the oscilloscope leaves two divisions of buffer room for whatever reason.
        print("<writing file>")
        with open(filename,'w') as fh:
            obj = {'times':list(out_t),
                   'values': list(out_v),
                   'variable':variable}
            strdata = json.dumps(obj,indent=4)
            fh.write(strdata)
        print("<wrote file>")


    def execute(self,state):
        if not state.dummy:
            props = state.oscilloscope.get_properties()
            chan = state.oscilloscope.analog_channel(self._chan_low)


            ch1 = state.oscilloscope.full_waveform(chan)

            ch2 = None
            if self._differential:
                chan = state.oscilloscope.analog_channel(self._chan_high)
                ch2 = state.oscilloscope.full_waveform(chan)

            return self.process_data(state,self._filename, \
                                     self._variable,
                                     ch1,ch2)


    def __repr__(self):
        if not self._differential:
            return "%s direct %d %s %s" % (self.name(),
                                        self._chan_low,
                                        self._variable,
                                        self._filename)
        else:
            return "%s differential %d %d %s %s" % (self.name(),
                                        self._chan_low,
                                        self._chan_high,
                                        self._variable,
                                        self._filename)



class OscSetSimTimeCmd(Command):

    def __init__(self,sim_time,frame_time=None):
        Command.__init__(self)
        self._sim_time = sim_time
        self._frame_time = (sim_time if frame_time is None else frame_time)

    @staticmethod
    def name():
        return 'osc_set_sim_time'

    def __repr__(self):
        return "%s %f" % (self.name(),self._sim_time)


    @staticmethod
    def parse(args):
        return strict_do_parse("{sim_time:f}", args, \
                               OscSetSimTimeCmd)


    def configure_oscilloscope(self,state,time_sec):
        frame_sec = time_sec
        # TODO: multiple segments of high sample rate.
        theo_time_per_div = float(time_sec) / state.oscilloscope.TIME_DIVISIONS
        act_time_per_div = state.oscilloscope \
                                .closest_seconds_per_division(theo_time_per_div)
        trig_delay = act_time_per_div * (float(state.oscilloscope.TIME_DIVISIONS/2.0))
        print("desired sec/div %s" % theo_time_per_div)
        print("actual sec/div %s" % act_time_per_div)
        print("sec: %s" % time_sec)
        print("delay: %s" % trig_delay)
        state.oscilloscope.set_seconds_per_division(theo_time_per_div)
        state.oscilloscope.set_trigger_delay(trig_delay)
        return frame_sec

    def execute(self,state):
        if not state.dummy:
            frame_time_sec = self.configure_oscilloscope(state,self._sim_time)
            self._frame_time = frame_time_sec

    @staticmethod
    def desc():
        return "set the number of samples to record (max 10000)"


    @staticmethod
    def desc():
        return "[oscilloscope] set the simulation time and input time"



class MicroSetSimTimeCmd(ArduinoCommand):

    def __init__(self,sim_time,input_time,frame_time=None):
        ArduinoCommand.__init__(self)
        if(sim_time <= 0):
            self.fail("invalid simulation time: %s" % n_samples)

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
        return "%s %f %f" % (self.name(),self._sim_time,self._input_time)


    @staticmethod
    def parse(args):
        return strict_do_parse("{sim_time:f} {input_time:f}", args, \
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

class OscSetupTrigger(Command):

    def __init__(self):
        Command.__init__(self)

    @staticmethod
    def name():
        return 'osc_setup_trigger'

    @staticmethod
    def desc():
        return "[oscilloscope] setup edge trigger on oscilloscope."



    @staticmethod
    def parse(args):
        return strict_do_parse("",args,OscSetupTrigger)


    def exec_setup_osc(self,state):
        if state.use_osc and not state.dummy:
            edge_trigger = osclib.Trigger(osclib.TriggerType.EDGE,
                                state.oscilloscope.ext_channel(),
                                osclib.HRTime(80e-7),
                                min_voltage=0.080,
                                which_edge=osclib
                                          .TriggerSlopeType
                                          .ALTERNATING_EDGES)
            state.oscilloscope.set_trigger(edge_trigger)
            state.oscilloscope.set_trigger_mode(osclib.TriggerModeType.NORM)

            trig = state.oscilloscope.get_trigger()
            print("trigger: %s" % trig)
            #state.oscilloscope.set_history_mode(True)
            props = state.oscilloscope.get_properties()
            print("== oscilloscope properties")
            for key,val in props.items():
                print("%s : %s" % (key,val))


    def __repr__(self):
        return self.name()


    def execute(self,state):
        self.exec_setup_osc(state)

class MicroSetupChipCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)


    @staticmethod
    def name():
        return 'micro_setup_chip'

    @staticmethod
    def desc():
        return "[microcontroller] calibrate+setup blocks/conns in chip."

    @staticmethod
    def parse(args):
        return strict_do_parse("",args,MicroSetupChipCmd)



    def __repr__(self):
        return self.name()


    def execute(self,state):
        for stmt in state.calibrate_chip():
            stmt.apply(state)

        for stmt in state.configure_chip():
            stmt.apply(state)


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


class MicroTeardownChipCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'micro_teardown_chip'

    @staticmethod
    def desc():
        return "[microcontroller] calibrate+teardown blocks/conns in chip."

    @staticmethod
    def parse(args):
        return strict_do_parse("",args,MicroTeardownChipCmd)

    def __repr__(self):
        return self.name()

    def execute(self,state):
        for stmt in state.teardown_chip():
            stmt.apply(state)


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

