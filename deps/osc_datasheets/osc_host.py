import socket
import time
import sys
import wave

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

    def __init__(self,ipaddr,port):
        self._sock = SocketConnect(ipaddr,port)
        self._ip = ipaddr
        self._port = port

    def setup(self):
        self.query("CHDR OFF")

    def _recvall(self):
        total_data=[];
        data=''
        eom='\n'
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

        return ''.join(total_data)


    def write(self,cmd):
        try :
            #Send cmd string
            print("-> %s" % cmd)
            self._sock.sendall(cmd)
            self._sock.sendall(b'\n')
            time.sleep(0.1)
        except socket.error:
            #Send failed
            print ('send failed <%s>' % cmd)
            sys.exit()

    def query(self,cmd):
        self.write(cmd)
        reply = self._recvall()
        return reply

    def identifier(self):
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

    def sample_status(self):
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
        else:
            raise Exception("unknown status <%s>" % args[0])

    def n_samples(self,channel_no):
        assert(isinstance(channel_no,int))
        cmd = 'SANU? C%d' % channel_no
        result = self.query(cmd)
        args = self._validate("SANU",result)   
        npts,unit = self._extract_number_and_unit(args[0])
        if unit == 'Mpts':
            return int(npts)*1e6
        else:
            raise Exception("<%s> unknown unit <%s>" % \
                    (args[0],unit))


    def sample_rate(self):
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

    def voltage_scale(self,channel_no):
        cmd = 'C%d:VDIV?' % channel_no
        result = self.query(cmd)
        args = self._validate("VDIV",result)
        tc = float(args[0])
        return tc

    def time_constant(self):
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

    def get_waveform_params(self):
        cmd = "WFSU?"
        result = self._dev.query(cmd)
        return result

    def get_waveform_format(self):
        cmd = "TEMPLATE?"
        self._dev.write(cmd)
        result = self._dev.read_raw()
        return result

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
        resp = self.query(cmd)
        idx = resp.index('#9')
        if(idx < 0):
            print(resp)
            raise Exception("could not find marker")
        idx_start = idx+2+9
        data_size = int(resp[idx+2:idx_start])
        data_str = resp[idx_start:idx_start+data_size]
        print("last: %d" % (idx_start+data_size))
        print("len:  %d" % len(data_str))

        times = map(lambda i: i*time_scale,
                    range(0,len(data_str)))
        values = map(lambda b:
                     b*voltage_scale/25.0+voltage_offset, \
                     bytearray(data_str))


        return list(times),list(values)

    def screendump(self,filename):
        cmd = "SCDP"
        result = self.query(cmd)
        with open(filename,'wb') as fh:
            fh.write(result)

    def close(self):
        self._sock.close()
        time.sleep(1)

def read_data(osc):
    osc.setup()
    ident = osc.identifier()
    status = osc.sample_status()
    samples = osc.n_samples(1)
    rate = osc.sample_rate()
    tc = osc.time_constant()
    volt_sc = osc.voltage_scale(1)
    #osc.set_waveform_params(0)
    print("status: %d" % status)
    print("# samples: %s samples" % samples)
    print("rate: %s samples/s" % rate)
    print("time-const: %s s/sample" % tc)
    print("volt_scale: %s V/unit" % volt_sc)
    osc.acquire()
    raw_input()
    osc.stop()
    times,values = osc.waveform(1)
    import matplotlib.pyplot as plt
    plt.plot(times,values)
    plt.savefig('data.png')
    raise NotImplementedError
    osc.screendump('test.bmp')
    #osc.acquire()
    print(osc.get_waveform_format())
    print("settings: %s" % osc.get_waveform_params())
    print(osc.identifier())

IP_ADDR = "128.30.71.122"
PORT = 5024
#REMOTE_OSC_IP = "TCPIP::%s::inst0::INSTR" % (IP_ADDR)
#OSC_ID = "USB0::62701::60986::SDS1EBBC2R0244::0::INSTR"

#print(REMOTE_OSC_IP)
#device = resources.open_resource(REMOTE_OSC_IP)
print("connecting")
osc = Sigilent1020XEOscilloscope(IP_ADDR,PORT)
try:
    print("reading data")
    read_data(osc)
finally:
    print("close socket..")
    osc.close()

