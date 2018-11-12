import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
from lib.base_command import Command,ArduinoCommand
import math
import construct
import matplotlib.pyplot as plt
import devices.sigilent_osc as osclib
import time

def build_exp_ctype(exp_data):
    return {
        'type':enums.CmdType.EXPERIMENT_CMD.name,
        'data': {
            'exp_cmd':exp_data
        }
    }



class ResetCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'reset'

    @staticmethod
    def desc():
        return "reset any set flags, values and buffers."

    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.RESET.name,
            'args':{
                'ints':[0,0,0]
            }
        })


    def execute(self,state):
        state.reset()
        ArduinoCommand.execute(self,state)


    @staticmethod
    def parse(args):
        if len(args) != 0:
            print("usage: %s" % (ResetCmd.name()))
            return None

        return ResetCmd()

    def __repr__(self):
        return "reset"

class UseDueADCCmd(ArduinoCommand):
    def __init__(self,adc_no):
        ArduinoCommand.__init__(self)
        self._adc_id = adc_no

    @staticmethod
    def name():
        return "use_due_adc"

    @staticmethod
    def desc():
        return "use the arduino's analog to digital converter."

    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_ADC.name,
            'args':{
                'ints':[self._adc_id,0,0]
            }
        })


    @staticmethod
    def parse(args):
        line = " ".join(args)
        result = parselib.parse("{arduino_adc:d}",line)
        if result is None:
            print("usage: %s <arduino_adc_id>" % (SetNumADCSamplesCmd.name()))
            return None

        return UseDueADCCmd(result['arduino_adc'])

    def execute(self,state):
        state.use_adc(self._adc_id)
        ArduinoCommand.execute(self,state)

    def __repr__(self):
        return "use_due_adc %d" % self._adc_id


class GetTimeBetweenSamplesCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'get_time_between_samples'

    @staticmethod
    def desc():
        return "get the time between samples"



    @staticmethod
    def parse(args):
        if len(args) > 0:
            print("usage: %s" % GetTimeBetweenSamplesCmd.name())
            return None

        return GetTimeBetweenSamplesCmd()


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.GET_TIME_BETWEEN_SAMPLES.name,
            'args':{
                'ints':[0,0,0]
            }
        })


    def execute(self,state):
        line = ArduinoCommand.execute(self,state)
        print(">> %s" % line)
        resp = state.arduino.readline()
        tb_samples = float(resp.strip())
        state.time_between_samples_ms = tb_samples
        print("time-between-samples: %s" % tb_samples)
        return tb_samples


class GetNumSamplesCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'get_num_samples'

    @staticmethod
    def desc():
        return "get the number of samples"



    @staticmethod
    def parse(args):
        if len(args) > 0:
            print("usage: %s" % GetNumSamplesCmd.name())
            return None

        return GetNumSamplesCmd()


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.GET_NUM_SAMPLES.name,
            'args':{
                'ints':[0,0,0]
            }
        })


    def execute(self,state):
        line = ArduinoCommand.execute(self,state)
        print(">> %s" % line)
        resp = state.arduino.readline()
        n_samples = int(resp.strip())
        state.n_samples = n_samples
        print("num-samples: %s" % n_samples)
        return n_samples


class GetDueADCValuesCmd(ArduinoCommand):

    def __init__(self,filename,differential=True):
        ArduinoCommand.__init__(self)
        self._filename = filename
        self._differential = differential

    @staticmethod
    def name():
        return 'get_due_adc_values'

    @staticmethod
    def desc():
        return "use the arduino's analog to digital converter."


    def execute_read_op(self,state,adc_id,n,offset):
        data_header = build_exp_ctype({
            'type':enums.ExpCmdType.GET_ADC_VALUES.name,
            'args':{
                'ints':[adc_id,n,offset]
            }
        })

        data_header_t = self._c_type
        byts = data_header_t.build(data_header)
        line = self.write_to_arduino(state,byts)
        data_pos = []
        data_neg = []
        if state.dummy:
            return range(0,n),range(-n,0)
        else:
            return data_pos,data_neg

    @staticmethod
    def parse(args):
        line = " ".join(args)
        types = ['differential','direct']
        result = parselib.parse("{type} {filename}",line)
        if result is None:
            print("usage: %s <differential|direct> <filename>" % (GetDueADCValuesCmd.name()))
            return None

        if not result['type'] in types:
            print("usage: %s <differential|direct> <filename>" % (GetDueADCValuesCmd.name()))
            return None

        is_diff = result['type'] == 'differential'
        return GetDueADCValuesCmd(result['filename'],
                               differential=is_diff)


    def plot_data(self,filename,data):
        time = data['time']
        for adc_id in data['adcs'].keys():
            pos = data['adcs'][adc_id]['pos']
            neg = data['adcs'][adc_id]['neg']
            plt.plot(time,pos,label="%d-pos" % adc_id)
            plt.plot(time,neg,label="%d-neg" % adc_id)

        plt.savefig(filename)
        plt.clf()

    def execute(self,state):
        n = state.n_samples
        buf = []
        chunksize_bytes = 1000;
        chunksize_shorts = int(chunksize_bytes/2)

        data = {}
        data['time'] = range(0,n)
        data['adcs'] = {}
        for adc_id in state.adcs_in_use():
            data_p = []
            data_n = []
            for offset in range(0,n,chunksize_shorts):
                datum_p,datum_n = self.execute_read_op(state,
                                     adc_id,
                                     chunksize_shorts,
                                     offset)
                data_p += datum_p
                data_n += datum_n

            data['adcs'][adc_id] = {'pos':data_p,'neg':data_n}

        self.plot_data("adc_data.png",data)
        return data


class UseDueDACCmd(ArduinoCommand):

    def __init__(self,dac_id):
        ArduinoCommand.__init__(self)
        self._dac_id = dac_id



    @staticmethod
    def name():
        return 'use_due_dac'

    @staticmethod
    def desc():
        return "use the arduino's digital to analog converter (time varying signal)."


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_DAC.name,
            'args':{
                'ints':[self._dac_id,0,0]
            }
        })


    def execute(self,state):
        state.use_dac(self._dac_id)
        ArduinoCommand.execute(self,state)


    @staticmethod
    def parse(args):
        line = " ".join(args)
        result = parselib.parse("{arduino_dac:d}",line)
        if result is None:
            print("usage: %s <arduino_dac_id>" % (UseDueDACCmd.name()))
            return None

        return UseDueDACCmd(result['arduino_dac'])


    def __repr__(self):
        return "use_due_dac %d" % self._dac_id



class SetDueDACValuesCmd(ArduinoCommand):

    def __init__(self,dacid,pyexpr):
        ArduinoCommand.__init__(self)
        self.dac_id = dacid
        self.pyexpr = pyexpr

    @staticmethod
    def name():
        return 'set_due_dac_values'


    @staticmethod
    def desc():
        return "set the dac values to an expression."


    @staticmethod
    def parse(args):
        def usage():
            print("set_due_dac <dacid> <expr(t)>")

        if len(args) < 2:
            usage()
            return None

        dacid = int(args[0])
        expr = " ".join(args[1:])
        return SetDueDACValuesCmd(dacid,expr)

    def execute_write_op(self,state,buf,offset):
        data_header = build_exp_ctype({
            'type':enums.ExpCmdType.SET_DAC_VALUES.name,
            'args':{
                'ints':[self.dac_id,len(buf),offset]
            }
        })

        data_header_t = self._c_type
        data_body_t = construct.Array(len(buf),
                                      construct.Float32l)
        byts_h = data_header_t.build(data_header)
        byts_d = data_body_t.build(buf)
        return self.write_to_arduino(state,byts_h + byts_d)


    def execute(self,state):
        n = state.n_samples
        buf = []
        chunksize_bytes = 1000;
        chunksize_floats = chunksize_bytes/4
        delta = state.time_between_samples_ms
        offset = 0
        for idx in range(0,n):
            args = {'t':idx*delta,'math':math}
            value = eval(self.pyexpr,args)
            buf.append(value)
            state.write_input(self.dac_id,idx*delta,value)
            if len(buf) == chunksize_floats:
                line = self.execute_write_op(state,buf,offset)
                print('  >> %s' % line)
                offset += len(buf)
                buf = []

        self.execute_write_op(state,buf,offset)


    def __repr__(self):
        return "set_due_dac_values %d %s" % (self.dac_id,self.pyexpr)


class GetOscValuesCmd(Command):

    def __init__(self,filename,differential=True):
        ArduinoCommand.__init__(self)
        self._filename = filename
        self._differential = differential

    @staticmethod
    def name():
        return 'get_osc_values'


    @staticmethod
    def desc():
        return "get the values read from an oscilloscope."


    @staticmethod
    def parse(args):
        line = " ".join(args)
        types = ['differential','direct']
        result = parselib.parse("{type} {filename}",line)
        if result is None:
            print("usage: %s <differential|direct> <filename>" % (GetOscValuesCmd.name()))
            return None

        if not result['type'] in types:
            print("usage: %s <differential|direct> <filename>" % (GetOscValuesCmd.name()))
            return None

        is_diff = result['type'] == 'differential'
        return GetOscValuesCmd(result['filename'],
                               differential=is_diff)

    def process_data(self,state,chan1,chan2):
        print("TODO: process data")

    def plot_data(self,state,filename,chan1,chan2):
        ch1_t,ch1_v = chan1
        for ident,time,value in state.input_data():
            plt.scatter(time,value,label="input_%s" % ident,s=1.0)

        plt.scatter(ch1_t,ch1_v,label="chan1",s=1.0)
        if not chan2 is None:
            ch2_t,ch2_v = chan2
            plt.scatter(ch2_t,ch2_v,label="chan2",s=1.0)

        ref_t,ref_v = state.reference_data()
        plt.scatter(ref_t,ref_v,label="ref",s=1.0)
        plt.legend()
        print("-> plotting")
        plt.savefig(filename)
        print("-> plotted")
        plt.clf()

    def execute(self,state):
        if not state.dummy:
            props = state.oscilloscope.get_properties()
            chan = state.oscilloscope.analog_channel(0)


            ch1 = state.oscilloscope.full_waveform(chan)

            ch2 = None
            if self._differential:
                chan = state.oscilloscope.analog_channel(1)
                ch2 = state.oscilloscope.full_waveform(chan)

            self.plot_data(state,"debug.png",ch1,ch2)
            return self.process_data(state,ch1,ch2)


    def __repr__(self):
        return "get_osc_values %s" % (self._filename)


class SetSimTimeCmd(ArduinoCommand):

    def __init__(self,sim_time,frame_time=None):
        ArduinoCommand.__init__(self)
        if(sim_time <= 0):
            self.fail("invalid simulation time: %s" % n_samples)

        self._sim_time = sim_time
        self._frame_time = sim_time if frame_time is None else frame_time


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.SET_SIM_TIME.name,
            'args':{
                'floats':[self._sim_time,self._frame_time,0]
            }
        })


    @staticmethod
    def name():
        return 'set_sim_time'

    @staticmethod
    def parse(args):
        line = " ".join(args)
        result = parselib.parse("{simtime_ms:f}",line)
        if result is None:
            print("usage: %s <# samples>" % (SetSimTimeCmd.name()))
            return None

        return SetSimTimeCmd(result['simtime_ms'])


    def configure_oscilloscope(self,state,time_ms):
        time_sec = time_ms/1000.0
        frame_sec = time_sec
        # TODO: multiple segments of high sample rate.
        time_per_div = float(time_sec) / state.oscilloscope.TIME_DIVISIONS
        trig_delay = time_per_div * float(state.oscilloscope.TIME_DIVISIONS/2.0)
        print("sec/div %s" % time_per_div)
        print("sec: %s" % time_sec)
        print("delay: %s" % trig_delay)
        state.oscilloscope.set_seconds_per_division(time_per_div)
        state.oscilloscope.set_trigger_delay(trig_delay)
        return frame_sec

    def execute(self,state):
        state.sim_time = self._sim_time
        if not state.dummy:
            frame_time_sec = self.configure_oscilloscope(state,self._sim_time)
            self._frame_time = frame_time_sec*1000.0

        ArduinoCommand.execute(self,state)



    @staticmethod
    def desc():
        return "set the number of samples to record (max 10000)"

    def __repr__(self):
        return "sim_time %d" % self._sim_time


class ComputeOffsetsCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'compute_offsets'

    @staticmethod
    def desc():
        return "compute the offsets for the data buffer. Must be completed before writing data to dacs/execution."


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.COMPUTE_OFFSETS.name,
            'args':{
                'ints':[0,0,0]
            }
        })


    def execute(self,state):
        ArduinoCommand.execute(self,state)

    @staticmethod
    def parse(args):
        if len(args) > 0:
            print("usage: %s" % ComputeOffsetsCmd.name())
            return None

        return ComputeOffsetsCmd()

    def __repr__(self):
        return self.name()


class UseAnalogChipCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'use_chip'

    @staticmethod
    def desc():
        return "mark the analog chip as used."


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_ANALOG_CHIP.name,
            'args':{
                'ints':[0,0,0]
            }
        })


    def execute(self,state):
        state.use_analog_chip = True
        ArduinoCommand.execute(self,state)

    @staticmethod
    def parse(args):
        if len(args) > 0:
            print("usage: %s" % UseAnalogChipCmd.name())
            return None

        return UseAnalogChipCmd()

    def __repr__(self):
        return self.name()


class UseADCCommand(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'use_ard_adc'

    @staticmethod
    def desc():
        return "enable recording samples read from ADCs."


    def execute(self,state):
        state.use_adc = True
        ArduinoCommand.execute(state)


class UseOscilloscopeCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'use_osc'

    @staticmethod
    def desc():
        return "enable recording values from oscilloscope."



    @staticmethod
    def parse(args):
        if len(args) > 0:
            print("usage: %s" % UseOscilloscopeCmd.name())
            return None

        return UseOscilloscopeCmd()

    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_OSC.name,
            'args':{
                'ints':[0,0,0]
            }
        })



    def execute(self,state):
        state.use_osc = True
        ArduinoCommand.execute(self,state)

    def __repr__(self):
        return self.name()


class RunCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)

    @staticmethod
    def name():
        return 'run'

    @staticmethod
    def desc():
        return "run the configured experiment."


    @staticmethod
    def parse(args):
        if len(args) > 0:
            print("usage: %s" % RunCmd.run())
            return None

        return RunCmd()

    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.RUN.name,
            'args':{
                'ints':[0,0,0]
            }
        })


    def execute(self,state):
        for stmt in state.calibrate_chip():
            print(stmt)
            stmt.apply(state)
        for stmt in state.configure_chip():
            print(stmt)
            stmt.apply(state)

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

        time.sleep(0.5)
        #input("<press enter to start>")
        line = ArduinoCommand.execute(self,state)
        if not state.dummy:
            while line is None or not "::done::" in line:
                print("resp:> %s" % line)
                line = state.arduino.readline()
            print("resp:> %s" % line)
            print("<done>")
            #input("<press enter to continue>")

        for stmt in state.teardown_chip():
            stmt.apply(state)

    def __repr__(self):
        return self.name()

