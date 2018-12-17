from devices.arduino_due import ArduinoDue
from devices.sigilent_osc import Sigilent1020XEOscilloscope
import devices.sigilent_osc as osclib

from lib.base_command import FlushCommand, ArduinoCommand
from lib.chip_command import AnalogChipCommand
import lib.util as util
import time
import numpy as np
import math

class State:

    def __init__(self,osc_ip,osc_port,ard_native,validate=False):
        if not validate:
            self.arduino = ArduinoDue(native=ard_native)
            self.oscilloscope = Sigilent1020XEOscilloscope(
                osc_ip, osc_port)
        self.prog = [];

        ## State committed to chip
        self.use_osc = False;

        self._use_adc = {};
        self._use_dac = {}
        self.use_analog_chip = None;
        self.inputs = {}
        self.n_dac_samples= None;
        self.n_adc_samples = None;
        self.time_between_samples_s = None;
        self.ref_func = None;
        self.reset();
        self.sim_time = None
        self.period = None
        self.dummy = validate

    def write_input(self,input_id,time_ms,value):
        if not input_id in self.inputs:
            self.inputs[input_id] = {'time':[],'value':[]}
        self.inputs[input_id]['time'].append(time_ms)
        self.inputs[input_id]['value'].append(value)

    def reference_data(self):
        if self.ref_func is None:
            return [],[]

        times = None
        for input_id,time,value in self.input_data():
            times = times if not times is None else time
            assert(len(time) == len(times))

        values = []
        print("reference: %s" % self.ref_func)
        if times is None:
            times = list(np.arange(0,self.sim_time,
                                   self.time_between_samples_s))

        for idx,time in enumerate(times):
            args = {'t':time,'i':idx}
            for input_id,_,value in self.input_data():
                args['inp%d' % input_id] = value[idx]
            result = util.eval_func(self.ref_func,args)
            values.append(result)


        return times,values

    def input_data(self):
        for input_id,data in self.inputs.items():
            yield input_id,data['time'],data['value']

    def reset(self):
        self.prog = []
        self.use_analog_chip = False;
        self.n_samples = 0
        self.ref_func = None
        self.inputs = {}
        for adc_id in range(0,4):
            self._use_adc[adc_id] = False

        self._use_dac = {}
        for dac_id in range(0,2):
            self._use_dac[dac_id] = False

    def use_dac(self,dac_id):
        self._use_dac[dac_id] = True

    def use_adc(self,adc_id):
        self._use_adc[adc_id] = True

    def adcs_in_use(self):
        for adc_id,in_use in self._use_adc.items():
            if in_use:
                yield adc_id

    def dacs_in_use(self):
        for dac_id,in_use in self._use_dac.items():
            if in_use:
                yield dac_id



    def close(self):
        if not self.dummy:
            self.arduino.close()
            self.oscilloscope.close()

    def initialize(self):
        if self.dummy:
            return

        try:
            print("[[ setup oscilloscope ]]")
            self.oscilloscope.setup()
        except Exception as e:
            print("[ERROR] %s" % e)
            print("[[no oscilloscope]]")
            self.oscilloscope = None

        try:
            print("[[ setup arduino ]]")
            self.arduino.open()
        except Exception as e:
            print("[ERROR] %s" % e)
            print("[[no arduino]]")
            self.arduino = None

        if not self.arduino is None:
            flush_cmd = FlushCommand()
            while not flush_cmd.execute(self):
                continue

    def enqueue(self,stmt):
        if stmt.test():
            print("[enq] %s" % stmt)
            self.prog.append(stmt)
        else:
            print("[error] " + stmt.error_msg())

    def calibrate_chip(self):
        if not self.use_analog_chip:
            return

        calibs = []
        for stmt in self.prog:
            if isinstance(stmt, AnalogChipCommand):
                calib_stmt = stmt.calibrate()
                if not calib_stmt is None:
                    calibs.append(calib_stmt)

        for calib in set(calibs):
            yield calib

    def teardown_chip(self):
        if not self.use_analog_chip:
            return

        for stmt in self.prog:
            if isinstance(stmt, AnalogChipCommand):
                dis_stmt = stmt.disable()
                if not dis_stmt is None:
                    yield dis_stmt

    def configure_chip(self):
        if not self.use_analog_chip:
            return

        for stmt in self.prog:
            if isinstance(stmt, AnalogChipCommand):
                print("[config] %s" % stmt)
                config_stmt = stmt.configure()
                if not config_stmt is None:
                    yield config_stmt



