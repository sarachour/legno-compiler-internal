import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
from lib.base_command import Command,ArduinoCommand
import math
import construct
import matplotlib.pyplot as plt

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
            'args':[0,0,0]
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
            'args':[self._adc_id,0,0]
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
            'args':[adc_id,n,offset]
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
            'args':[self._dac_id,0,0]
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
            'args':[self.dac_id,len(buf),offset]
        })

        data_header_t = self._c_type
        data_body_t = construct.Array(len(buf),
                                      construct.Float32l)
        byts_h = data_header_t.build(data_header)
        byts_d = data_body_t.build(buf)
        self.write_to_arduino(state,byts_h + byts_d)


    def execute(self,state):
        n = state.n_samples
        buf = []
        chunksize_bytes = 1000;
        chunksize_floats = chunksize_bytes/4
        delta = state.TIME_BETWEEN_SAMPLES
        offset = 0
        for idx in range(0,n):
            args = {'t':idx*delta,'math':math}
            value = eval(self.pyexpr,args)
            buf.append(value)
            if len(buf) == chunksize_floats:
                self.execute_write_op(state,buf,offset)
                buf = []
                offset += len(buf)

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

    def process_data(self,chan1,chan2,clock):
        clk_t,clk_v = clock
        threshold = (max(clk_v) + min(clk_v))/2.0
        is_high = lambda q: q > threshold
        times = []
        print("threshhold=%s" % threshold)
        clk_dir = is_high(clk_v[0])
        print("-> finding clock changes")
        for time,value in zip(clk_t,clk_v):
            curr_clk_dir = is_high(value)
            if curr_clk_dir != clk_dir:
                times.append(time)
                clk_dir = curr_clk_dir
        print("times: %s" % times)
        start_time = times[0]
        end_time = times[-1]
        print("-> computing signal from t=[%s,%s]" % \
              (start_time,end_time))
        if chan2 is None:
            times,values = chan2
        else:
            values = []
            times = []
            for (ch1_t,ch1_v),(ch2_t,ch2_v) in zip(chan1,chan2):
                assert(ch1_t == ch2_t)
                if ch1_t < start_time or ch1_t > end_time:
                    continue

                values.append[ch1_v - ch2_v]
                times.append(ch1_t)

        return times,values

    def plot_data(self,filename,chan1,chan2,clock):
        ch1_t,ch1_v = chan1
        plt.plot(ch1_t,ch1_v,label="chan1")
        if not chan2 is None:
            ch2_t,ch2_v = chan2
            plt.plot(ch2_t,ch2_v,label="chan2")

        clk_t,clk_v = clock
        plt.plot(clk_t,clk_v,label="clk")
        plt.savefig(filename)
        plt.clk()
        input()

    def execute(self,state):
        if not state.dummy:
            props = state.oscilloscope.get_properties()
            chan = state.oscilloscope.analog_channel(0)


            ch1 = state.oscilloscope.waveform(chan,
                voltage_scale=props['voltage_scale'][chan],
                time_scale=props['time_scale'],
                voltage_offset=props['voltage_offset'][chan]
            )

            if self._differential:
                chan = state.oscilloscope.analog_channel(1)
                ch2 = state.oscilloscope.waveform(
                    state.oscilloscope.analog_channel(1),
                    voltage_scale=props['voltage_scale'][chan],
                    time_scale=props['time_scale'],
                    voltage_offset=props['voltage_offset'][chan]
                )

            chan = state.oscilloscope.digital(1)
            clk = state.oscilloscope.waveform(
                state.oscilloscope.ext_channel(),
                voltage_scale=props['voltage_scale'][chan],
                time_scale=props['time_scale'],
                voltage_offset=props['voltage_offset'][chan]
            )
            self.plot_data(self,"debug.png",ch1,ch2,clk)
            return self.process_data(ch1,ch2,clk)


    def __repr__(self):
        return "get_osc_values %s" % (self._filename)


class SetNumADCSamplesCmd(ArduinoCommand):

    def __init__(self,n_samples):
        ArduinoCommand.__init__(self)
        if(n_samples <= 0):
            self.fail("unknown number of samples: %s" % n_samples)

        self._n_samples = n_samples


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.SET_N_ADC_SAMPLES.name,
            'args':[self._n_samples,0,0]
        })


    @staticmethod
    def name():
        return 'set_samples'

    @staticmethod
    def parse(args):
        line = " ".join(args)
        result = parselib.parse("{nsamples:d}",line)
        if result is None:
            print("usage: %s <# samples>" % (SetNumADCSamplesCmd.name()))
            return None

        return SetNumADCSamplesCmd(result['nsamples'])


    def execute(self,state):
        state.n_samples = self._n_samples
        ArduinoCommand.execute(self,state)



    @staticmethod
    def desc():
        return "set the number of samples to record (max 10000)"

    def __repr__(self):
        return "n_samples %d" % self._n_samples


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
            'args':[0,0,0]
        })


    def execute(self,state):
        ArduinoCommand.execute(self,state)

    @staticmethod
    def parse(args):
        if len(args) > 0:
            print("usage: %s" % ComputeOffsetsCmd.name())
            return None

        return UseAnalogChipCmd()

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
            'args':[0,0,0]
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
            print("usage: %s" % UseOscilloscopeCmd.run())
            return None

        return UseOscilloscopeCmd()

    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_OSC.name,
            'args':[0,0,0]
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
            'args':[0,0,0]
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
                                osclib.HRTime(80e-10),
                                min_voltage=0.068,
                                which_edge=osclib
                                          .TriggerSlopeType
                                          .ALTERNATING_EDGES)
            state.oscilloscope.set_trigger(edge_trigger)
            state.oscilloscope.set_trigger_mode(osclib.TriggerModeType.NORM)
            state.oscilloscope.set_history_mode(True)
            props = state.oscilloscope.get_properties()
            print("== oscilloscope properties")
            for key,val in props.items():
                print("%s : %s" % (key,val))

        #input("<press enter to start>")
        ArduinoCommand.execute(self,state)

        if state.use_osc and not state.dummy:
            state.oscilloscope.acquire()

        for stmt in state.teardown_chip():
            stmt.apply(state)

    def __repr__(self):
        return self.name()

