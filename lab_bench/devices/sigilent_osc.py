import sys
import logging
import socket
import argparse
import time
import wave # https://docs.python.org/2/library/wave.html

from enum import Enum

logging.basicConfig()

logger = logging.getLogger('osc')
logger.setLevel(logging.INFO)

def extract_number_and_unit(st):
    for i,c in enumerate(st):
        if not c.isdigit() and \
                not c == '.' and \
                not c == 'E' and\
                not c == '-':
            break
    number = float(st[:i])
    unit = st[i:]
    return number,unit

# use python 2
def SocketConnect(ipaddr,port):
    try:
        #create an AF_INET, STREAM socket (TCP)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print ('Failed to create socket.')
        sys.exit();
    try:
        #Connect to remote server
        s.connect((ipaddr, port))
    except socket.error:
        print ('failed to connect to ip ' + ipaddr)
        sys.exit(1)

    return s

def pairwise(arr):
    for idx in range(0,len(arr)-1,2):
        yield arr[idx],arr[idx+1]

class HoldType(Enum):
        TIME = "TI"
        OFF = "OFF"
        PULSE_SMALLER = "PS"
        PULSE_LARGER = "PL"
        PULSE_IN_RANGE = "P2"
        PULSE_OUT_OF_RANGE = "P1"
        INTERVAL_SMALLER = "IS"
        INTERVAL_LARGER = "IL"
        INTERVAL_IN_RANGE = "I2"
        INTERVAL_OUT_OF_RANGE = "I1"

class HoldRule:

    def __init__(self,hold_type,value1,value2=None):
            self._hold_type = hold_type
            self._value1 = value1
            self._value2 = value2
    
    def to_cmd(self):
        cmd = "HT,%s,HV,%ss" % (self._hold_type.value,self._value1)
        if not self._value2 is None:
            cmd += ",HV2,%ss" % self._value2
        return cmd

    @staticmethod
    def build(holdtype,value1,value2):
        if holdtype == HoldType.TIME:
            return HRTime(value1)
        elif holdtype == HoldType.OFF:
           return HROff()
        else:
            raise Exception("unhandled: %s" % holdtype)

class HRTime(HoldRule):

    def __init__(self,value):
        HoldRule.__init__(self,HoldType.TIME,value,None)
        self._time = value

    def __repr__(self):
        return "t>%s" % self._time


class HROff(HoldRule):

    def __init__(self):
        HoldRule__init__(self,HoldType.OFF,0.0,None)
        pass

    def __repr__(self):
        return "off"

class TriggerType(Enum):
    EDGE = "EDGE"

class TriggerSlopeType(Enum):
    FALLING_EDGE = "NEG"
    RISING_EDGE = "POS"
    ALTERNATING_EDGES = "WINDOW"

class Trigger:
    def __init__(self,trigger_type,source,hold_rule,
                 min_voltage=None,
                 which_edge=None):
        self.trigger_type = trigger_type
        self.source = source
        self.when = hold_rule
        self.min_voltage = min_voltage
        self.which_edge = which_edge

    def to_cmds(self):
        yield "TRIG_SELECT %s,SR,%s,%s" % \
            (self.trigger_type.value,
             self.source.value,
             self.when.to_cmd())

        if not self.which_edge is None:
            yield "TRIG_SLOPE %s" % self.which_edge.value

        if not self.min_voltage is None:
            yield "TRIG_LEVEL %s" % self.min_voltage

    @staticmethod
    def build(args):
        scaling = {'ms':1e-3,'s':1.0}
        trigger_type = TriggerType(args[0])
        props = dict(pairwise(args[1:]))
        # TI:time (OFF or TI)
        # HT:hold type
        # HV:hold value
        # SR:source
        chan = Sigilent1020XEOscilloscope.Channels(props['SR'])
        ht = HoldType(props['HT'])
        hv,unit = extract_number_and_unit(props['HV'])
        value = float(hv)*1e-3*scaling[unit]
        if 'HV2' in props:
            hv2,unit2 = extract_number_and_unit(props['HV2'])
            value2 = float(hv2)*1e-3*scaling[unit2]
        else:
            value2 = None

        hold_rule = HoldRule.build(ht,value,value2)
        return Trigger(trigger_type,chan,hold_rule)

    def __repr__(self):
        return "trigger[%s](%s) when=%s which_edge=%s min-volt=%s" % \
            (self.trigger_type.name,
             self.source,
             self.when,
             self.which_edge,
             self.min_voltage)


class TriggerModeType(Enum):
    AUTO = "AUTO";
    NORM = "NORM";
    SINGLE = "SINGLE";
    STOP = "STOP"

class Sigilent1020XEOscilloscope:
    class Channels(Enum):
        ACHAN1 = "C1",
        ACHAN2 = "C2",
        EXT = "EX"
        EXT5 = "EX5"
        LINE = "LINE"

    class OscStatus(Enum):
        READY = "Ready";
        TRIGGERED = "Trig'd";
        STOP = "Stop";
        AUTO = "Auto";
        ARM = "Arm";
        ROLL = "Roll";


    def __init__(self,ipaddr,port):
        self._ip = ipaddr
        self._port = port
        self._analog_channels = [
            Sigilent1020XEOscilloscope.Channels.ACHAN1,
            Sigilent1020XEOscilloscope.Channels.ACHAN2,
        ]
        self._digital_channels = [
            Sigilent1020XEOscilloscope.Channels.EXT
        ]
        self._channels = self._analog_channels + self._digital_channels
        self._prop_cache = None

    def flush_cache(self):
        self._prop_cache = None

    def analog_channel(self,idx):
        if idx == 0:
            return Sigilent1020XEOscilloscope.Channels.ACHAN1
        elif idx == 1:
            return Sigilent1020XEOscilloscope.Channels.ACHAN2

        else:
            raise Exception("unknown analog channel.")

    def get_trigger(self):
        cmd = "TRIG_SELECT?"
        result = self.query(cmd)
        if ">>" in result:
            result = result.split(">>")[-1].strip()

        tokens = result.split(",")
        trig = Trigger.build(tokens)

        cmd = "%s:TRIG_LEVEL?" % (trig.source.value)
        result = self.query(cmd)
        trig.min_voltage = float(result.strip())

        cmd = "%s:TRIG_SLOPE?" % (trig.source.value)
        result = self.query(cmd)
        trig.which_edge = TriggerSlopeType(result.strip())
        return trig

    def get_trigger_mode(self):
        cmd = "TRIG_MODE?"
        result = self.query(cmd)
        status = TriggerModeType(result.strip())
        return status

    def set_trigger_mode(self,mode):
        cmd = "TRIG_MODE %s" % mode.value
        self.write(cmd)

    def get_history_frame_time(self):
        cmd = "FTIM?"
        resp = self.query(cmd)
        print(resp)

    def set_history_frame(self,idx):
        cmd = "FRAM %d" % idx
        self.write(cmd)

    def set_trigger(self,trigger):
        assert(isinstance(trigger,Trigger))
        for cmd in trigger.to_cmds():
            result = self.write(cmd)
        return

    def set_history_mode(self,enable):
        cmd = "HSMD %s" % ("ON" if enable else "OFF")
        self.write(cmd)

    def get_history_mode(self):
        cmd = "HSMD?"
        result = self.query(cmd)
        if result == "ON":
            return True
        elif result == "OFF":
            return False
        else:
            raise Exception("unexpected response <%s>" % result)

    def ext_channel(self):
        return Sigilent1020XEOscilloscope.Channels.EXT

    def setup(self):
        self._sock = SocketConnect(self._ip,self._port)
        self.query("CHDR OFF")

    def _recvall(self):
        total_data=[];
        data=''
        eom=b'\n'
        while True:
            data=self._sock.recv(4096)
            if eom in data:
                seg = data[:data.find(eom)]
                total_data.append(seg)
                break

            total_data.append(data)
            if len(total_data) > 1:
                #check if end_of_data was split
                last_pair=total_data[-2]+total_data[-1]
                if eom in last_pair:
                    total_data[-2]=last_pair[:last_pair.find(eom)]
                    total_data.pop()
                    break


        ba = bytearray([])
        for datum in total_data:
            ba += datum

        return ba


    def write(self,cmd):
        try :
            #Send cmd string
            print("-> %s" % cmd)
            self._sock.sendall(bytes(cmd,'UTF-8'))
            self._sock.sendall(b'\n')
            time.sleep(0.1)
        except socket.error:
            #Send failed
            print ('send failed <%s>' % cmd)
            sys.exit()

    def query(self,cmd,decode='UTF-8'):
        self.write(cmd)
        reply = self._recvall()
        if not decode is None:
            return reply.decode(decode)
        else:
            return reply

    def get_identifier(self):
        return self.query("*IDN?")

    def _validate(self,cmd,result):
        args = result.strip().split()
        return args

    def get_sample_status(self):
        cmd = "SAST?"
        result = self.query(cmd)
        args = self._validate("SAST",result)
        status = Sigilent1020XEOscilloscope.OscStatus(args[0])
        if status is None:
            raise Exception("unknown status <%s>" % args[0])
        return status

    def get_n_samples(self,channel):
        assert(channel in self._channels)
        cmd = 'SANU? %s' % channel.value
        result = self.query(cmd)
        args = self._validate("SANU",result)
        npts,unit = extract_number_and_unit(args[0])
        if unit == 'Mpts':
            return int(npts)*1e6
        if unit == 'kpts':
            return int(npts)*1e3
        else:
            raise Exception("<%s> unknown unit <%s>" % \
                    (args[0],unit))


    def get_sample_rate(self):
        cmd = 'SARA?'
        result = self.query(cmd)
        args = self._validate("SARA",result)
        rate,unit = extract_number_and_unit(args[0])
        if unit == 'Sa/s':
            return rate
        elif unit == "GSa/s":
            return rate*1e9
        elif unit == "MSa/s":
            return rate*1e6
        else:
            raise Exception("unknown unit <%s>" % unit)

    def get_voltage_scale(self,channel):
        assert(channel in self._channels)
        cmd = '%s:VDIV?' % channel.value
        result = self.query(cmd)
        args = self._validate("VDIV",result)
        tc = float(args[0])
        return tc

    def get_time_constant(self):
        cmd = 'TDIV?' 
        result = self.query(cmd)
        args = self._validate("TDIV",result)
        tc = float(args[0])
        return tc


    def set_waveform_params(self,n_pts,start=0,stride=0,
                            all_points_in_memory=False):
        cmd = "WFSU SP,%d,NP,%d,FP,%d" % (stride,n_pts,start)
        result = self.write(cmd)
        cmd = "WFSU TYPE,%d" % (0 if not all_points_in_memory else 1)
        result = self.write(cmd)

    def get_voltage_offset(self,channel):
        assert(channel in self._channels)
        cmd = "%s:OFST?" % channel.value
        result = self.query(cmd)
        args = self._validate("OFST",result)
        off = float(args[0])
        return off

    def get_waveform_params(self):
        cmd = "WFSU?"
        result = self._dev.query(cmd)
        return result

    def get_waveform_format(self):
        cmd = "TEMPLATE?"
        self._dev.write(cmd)
        result = self._dev.read_raw()
        return result

    def get_properties(self):
        if not self._prop_cache is None:
            return self._prop_cache

        ident = self.get_identifier()
        status = self.get_sample_status()
        rate = self.get_sample_rate()
        time_const = self.get_time_constant()
        channels = self._channels
        samples = {}
        volt_scale = {}
        offset = {}
        for channel in self._analog_channels:
            samples[channel.name] = self.get_n_samples(channel)
            volt_scale[channel.name] = self.get_voltage_scale(channel)
            offset[channel.name] = self.get_voltage_offset(channel)

        self._prop_cache = {
            'identifier': ident,
            'status': status,
            'sample_rate': rate,
            'time_scale':time_const,
            'channels':channels,
            'n_samples':samples,
            'voltage_scale':volt_scale,
            'voltage_offset':offset
        }
        return self._prop_cache

    def acquire(self):
        resp = self.query("INR?")
        print(resp)
        resp = self.query("INR?")
        print(resp)
        self.write("ARM")

    def stop(self):
        self.write("STOP")


    def auto(self):
        self.write("AUTO")

    def set_history_list_open(self,v):
        cmd = "HSLST %s" % ("ON" if v else "OFF")
        self.write(cmd)

    def is_history_list_open(self):
        cmd = "HSLST?"
        resp = self.query(cmd)
        return True if resp == "ON" else False

    def waveform(self,channel,voltage_scale=1.0,time_scale=1.0,voltage_offset=0.0):
        assert(channel in self._channels)
        cmd = "%s:WF? DAT2" % channel.value
        resp = self.query(cmd,decode=None)
        code_idx = None
        for idx,byte in enumerate(resp):
            chrs = chr(byte)
            chrs += chr(resp[idx+1])
            if chrs == '#9':
                code_idx = idx
                break

        if(code_idx is None):
            raise Exception("could not find marker")

        idx_start = code_idx+2+9
        data_size = int(resp[idx+2:idx_start])
        data_ba = resp[idx_start:idx_start+data_size]

        times = map(lambda i: i*time_scale,
                    range(0,len(data_ba)))
        values = map(lambda b:
                     b*voltage_scale/25.0-voltage_offset, \
                     data_ba)


        return list(times),list(values)

    def screendump(self,filename):
        cmd = "SCDP"
        result = self.query(cmd)
        with open(filename,'wb') as fh:
            fh.write(result)

    def close(self):
        self._sock.close()
        time.sleep(1)
