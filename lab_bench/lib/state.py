from devices.arduino_due import ArduinoDue
from devices.sigilent_osc import Sigilent1020XEOscilloscope
import devices.sigilent_osc as osclib

from lib.base_command import FlushCommand, ArduinoCommand
from lib.chip_command import AnalogChipCommand, Priority
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
        else:
            self.arduino = None
            self.oscilloscope = None

        self.prog = [];

        ## State committed to chip
        self.use_osc = False;

        self._use_adc = {};
        self._use_dac = {}
        self._overflow = {}
        self.use_analog_chip = None;
        self.n_dac_samples= None;
        self.n_adc_samples = None;
        self.time_between_samples_s = None;


        self.reset();
        self.sim_time = None
        self.input_time = None
        self.dummy = validate

    def set_overflow(self,handle,oflow):
        self._overflow[handle] = oflow

    def overflows(self):
        for handle,oflow in self._overflow.items():
            yield handle,oflow


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
        if not self.arduino is None:
            self.arduino.close()
        if not self.oscilloscope is None:
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

    def order(self,insts):
        pq = {}
        priorities = [Priority.FIRST, \
                      Priority.EARLY, \
                      Priority.NORMAL, \
                      Priority.LATE,
                      Priority.LAST]

        for prio in priorities:
            pq[prio] = []

        for inst in insts:
            prio = inst.priority()
            pq[prio].append(inst)

        for prio in priorities:
            for inst in pq[prio]:
                yield inst


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

        for calib in self.order(set(calibs)):
            print("[calibrate] %s" % stmt)
            yield calib

    def analyze_chip(self):
        if not self.use_analog_chip:
            return

        hooks = []
        for stmt in self.prog:
            if isinstance(stmt, AnalogChipCommand):
                hook_stmt = stmt.analyze()
                if not hook_stmt is None:
                    hooks.append(hook_stmt)

        for hook in self.order(set(hooks)):
            print("[analyze] %s" % hook)
            yield hook


    def teardown_chip(self):
        if not self.use_analog_chip:
            return

        teardown = []
        for stmt in self.prog:
            if isinstance(stmt, AnalogChipCommand):
                dis_stmt = stmt.disable()
                if not dis_stmt is None:
                    teardown.append(dis_stmt)

        for tstmt in self.order(set(teardown)):
            print("[teardown] %s" % tstmt)
            yield tstmt

    def configure_chip(self):
        if not self.use_analog_chip:
            return

        cfg = []
        for stmt in self.prog:
            if isinstance(stmt, AnalogChipCommand):
                config_stmt = stmt.configure()
                if not config_stmt is None:
                    cfg.append(config_stmt)

        for cfgstmt in self.order(set(cfg)):
            print("[config] %s" % cfgstmt)
            yield cfgstmt



