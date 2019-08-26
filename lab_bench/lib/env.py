from lab_bench.devices.arduino_due import ArduinoDue
from lab_bench.devices.sigilent_osc import Sigilent1020XEOscilloscope
import lab_bench.devices.sigilent_osc as osclib

from lab_bench.lib.chipcmd.data import CalibType
from lab_bench.lib.base_command import FlushCommand, ArduinoCommand
from lab_bench.lib.base_command import AnalogChipCommand
import lab_bench.lib.util as util
import lab_bench.lib.chipcmd.state as state
import time
import numpy as np
import math

class GrendelEnv:

    def __init__(self,osc_ip,osc_port,ard_native, \
                 validate=False, \
                 calib_mode=CalibType.MIN_ERROR):
        if not validate:
            self.arduino = ArduinoDue(native=ard_native)
            self.oscilloscope = Sigilent1020XEOscilloscope(
                osc_ip, osc_port)
        else:
            self.arduino = None
            self.oscilloscope = None


        ## State committed to chip
        self.use_osc = False;
        self.calib_mode = calib_mode

        self.state_db = state.BlockStateDatabase()
        self._use_adc = {};
        self._use_dac = {}
        self.use_analog_chip = None;
        self.n_dac_samples= None;
        self.n_adc_samples = None;
        self.time_between_samples_s = None;
        self._status = {}

        self.reset();
        self.sim_time = None
        self.input_time = None
        self.dummy = validate

    def set_status(self,handle,oflow):
        self._status[handle] = oflow

    def statuses(self):
        for handle,oflow in self._status.items():
            yield handle,oflow


    def reset(self):
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
        if not self.arduino is None:
            self.arduino.close()
        if not self.oscilloscope is None:
            self.oscilloscope.close()

    def initialize(self):
        if self.dummy:
            return

        #try:
        print("[[ setup oscilloscope ]]")
        self.oscilloscope.setup()
        if not self.oscilloscope.ready():
            print("[[no oscilloscope]]")
            self.oscilloscope = None

        self.arduino.open()
        if not self.arduino.ready():
            print("[[no arduino]]")
            self.arduino = None

        if not self.arduino is None:
            flush_cmd = FlushCommand()
            while not flush_cmd.execute(self):
                continue

