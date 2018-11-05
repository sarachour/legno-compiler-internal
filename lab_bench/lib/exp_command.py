import parse as parselib
import lib.cstructs as cstructs
import lib.enums as enums
from lib.base_command import Command,ArduinoCommand
import math
import construct

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

class UseDueADCCmd(ArduinoCommand):

    def __init__(self):
        ArduinoCommand.__init__(self)


    @staticmethod
    def name():
        return 'use_due_adc'

    @staticmethod
    def desc():
        return "use the arduino's analog to digital converter."



class UseDueDACCmd(ArduinoCommand):

    def __init__(self,dac_id):
        ArduinoCommand.__init__(self)
        self._dac_id = dac_id



    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.USE_DAC.name,
            'args':[self._dac_id,0,0,0]
        })


    @staticmethod
    def name():
        return 'use_due_dac'

    @staticmethod
    def desc():
        return "use the arduino's digital to analog converter (time varying signal)."

    @staticmethod
    def parse(args):
        line = " ".join(args)
        result = parselib.parse("{arduino_dac:d}",line)
        if result is None:
            print("usage: %s <arduino_dac_id>" % (SetNumADCSamplesCmd.name()))
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
        return "set the dac values (up to 4096)."


    @staticmethod
    def parse(args):
        def usage():
            print("set_due_dac <dacid> <expr(t)>")

        if len(args) < 2:
            usage()
            return None

        dacid = int(args[0])
        expr = args[1]
        return SetDueDACValuesCmd(dacid,expr)

    def execute_arduino(self,state,buf,offset):
        data_header = build_exp_ctype({
            'type':enums.ExpCmdType.SET_DAC_VALUES.name,
            'args':[self.dac_id,len(buf),offset,0]
        })

        data_t = construct.Sequence(self._c_type,
                           construct.Array(len(buf),
                                           construct.Float32b))

        byts = data_t.build([data_header,buf])
        self.write_to_arduino(state,byts)


    def execute(self,state):
        n = state.n_samples
        buf = []
        chunksize = 4096
        delta = state.TIME_BETWEEN_SAMPLES
        offset = 0
        for idx in range(0,n):
            args = {'t':idx*delta,'math':math}
            value = eval(self.pyexpr,args)
            buf.append(value)
            if len(buf) == chunksize:
                self.execute_arduino(state,buf,offset)
                buf = []
                offset += len(buf)

        self.execute_arduino(state,buf,offset)


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

    def execute(self,state):
        if not self.dummy:
            props = osc.get_properties()
            ch1 = state.oscilloscope.waveform(1,
                voltage_scale=props['voltage_scale'][channel_no],
                time_scale=props['time_scale'],
                voltage_offset=props['voltage_offset'][channel_no])


            ch2 = state.oscilloscope.waveform(2,
                voltage_scale=props['voltage_scale'][channel_no],
                time_scale=props['time_scale'],
                voltage_offset=props['voltage_offset'][channel_no])

            clk = state.oscilloscope.digital(1)


    def __repr__(self):
        return "get_osc_values %s" % (self._filename)


class GetDueADCValuesCmd(ArduinoCommand):

    def __init__(self,filename):
        ArduinoCommand.__init__(self)
        self._filename = filename

    @staticmethod
    def name():
        return 'get_due_adc_values'


    @staticmethod
    def desc():
        return "get the values read from an adc (up to 4096)."


    @staticmethod
    def parse(args):
        line = " ".join(args)
        result = parselib.parse("{filename:w}",line)
        if result is None:
            print("usage: %s <filename>" % (GetADCValuesCmd.name()))
            return None

        return GetADCValuesCmd(result['filename'])



class SetNumADCSamplesCmd(ArduinoCommand):

    def __init__(self,n_samples):
        ArduinoCommand.__init__(self)
        if(n_samples <= 0):
            self.fail("unknown number of samples: %s" % n_samples)

        self._n_samples = n_samples


    def build_ctype(self):
        return build_exp_ctype({
            'type':enums.ExpCmdType.SET_N_ADC_SAMPLES.name,
            'args':[self._n_samples,0,0,0]
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
            'args':[0,0,0,0]
        })


    def execute(self,state):
        state.use_analog_chip = True
        ArduinoCommand.execute(self,state)

    @staticmethod
    def parse(args):
        if len(args) > 0:
            print("usage: %s" % UseAnalogChipCmd.run())
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
            'args':[0,0,0,0]
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
            'args':[0,0,0,0]
        })


    def execute(self,state):
        for stmt in state.calibrate_chip():
            print(stmt)
            stmt.apply(state)
        for stmt in state.configure_chip():
            print(stmt)
            stmt.apply(state)

        if state.use_osc and not state.dummy:
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

