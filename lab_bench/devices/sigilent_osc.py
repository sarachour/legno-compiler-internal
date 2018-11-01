import sys
import logging
import socket
import argparse
import time
import wave # https://docs.python.org/2/library/wave.html

import visa # https://pyvisa.readthedocs.io


logging.basicConfig()

logger = logging.getLogger('osc')
logger.setLevel(logging.INFO)


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

class Sigilent1020XEOscilloscope:
    class Status:
        READY = 0;
        TRIGGERED = 1;
        STOP = 2;
        AUTO = 3;
        ARM = 4;
        ROLL = 5;

    def __init__(self,ipaddr,port):
        self._sock = SocketConnect(ipaddr,port)
        self._ip = ipaddr
        self._port = port
        self._channels = [1,2]

    def setup(self):
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

    def _extract_number_and_unit(self,st):
        for i,c in enumerate(st):
            if not c.isdigit() and \
                    not c == '.' and \
                    not c == 'E' and\
                    not c == '-':
                break
        print(st)
        number = float(st[:i])
        unit = st[i:]
        return number,unit

    def _validate(self,cmd,result):
        args = result.strip().split()
        return args

    def get_sample_status(self):
        cmd = "SAST?"
        result = self.query(cmd)
        args = self._validate("SAST",result)
        if args[0] == "Trig'd":
            return Sigilent1020XEOscilloscope.Status.TRIGGERED
        elif args[0] == 'Ready':
            return Sigilent1020XEOscilloscope.Status.READY
        elif args[0] == 'Stop':
            return Sigilent1020XEOscilloscope.Status.STOP
        elif args[0] == 'Auto':
            return Sigilent1020XEOscilloscope.Status.AUTO
        elif args[0] == 'Arm':
            return Sigilent1020XEOscilloscope.Status.ARM
        elif args[0] == 'Roll':
            return Sigilent1020XEOscilloscope.Status.ROLL
        else:
            raise Exception("unknown status <%s>" % args[0])

    def get_n_samples(self,channel_no):
        assert(isinstance(channel_no,int))
        assert(channel_no in self._channels)
        cmd = 'SANU? C%d' % channel_no
        result = self.query(cmd)
        args = self._validate("SANU",result)
        npts,unit = self._extract_number_and_unit(args[0])
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
        rate,unit = self._extract_number_and_unit(args[0])
        if unit == 'Sa/s':
            return rate
        elif unit == "GSa/s":
            return rate*1e9
        elif unit == "MSa/s":
            return rate*1e6
        else:
            raise Exception("unknown unit <%s>" % unit)

    def get_voltage_scale(self,channel_no):
        assert(channel_no in self._channels)
        cmd = 'C%d:VDIV?' % channel_no
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

    def get_voltage_offset(self,channel_no):
        assert(channel_no in self._channels)
        cmd = "C%d:OFST?" % channel_no
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
        ident = self.get_identifier()
        status = self.get_sample_status()
        rate = self.get_sample_rate()
        time_const = self.get_time_constant()
        channels = self._channels
        samples = {}
        volt_scale = {}
        offset = {}
        for idx,channel_no in enumerate([1,2]):
            samples[channel_no] = self.get_n_samples(channel_no)
            volt_scale[channel_no] = self.get_voltage_scale(channel_no)
            offset[channel_no] = self.get_voltage_offset(channel_no)

        return {
            'identifier': ident,
            'status': status,
            'sample_rate': rate,
            'time_scale':time_const,
            'channels':channels,
            'n_samples':samples,
            'voltage_scale':volt_scale,
            'voltage_offset':offset
        }

    channels = [1,2]
    def acquire(self):
        resp = self.query("INR?")
        print(resp)
        resp = self.query("INR?")
        print(resp)
        self.write("ARM")

    def stop(self):
        self.write("STOP")

    def waveform(self,channel_no,voltage_scale=1.0,time_scale=1.0,voltage_offset=0.0):
        assert(isinstance(channel_no,int))
        cmd = "C%d:WF? DAT2" % channel_no
        resp = self.query(cmd,decode=None)
        print("<response>")
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
