import serial
import time
import re

class ArduinoDue:

    def __init__(self,native=True):
        self._baud_rate = 115200
        if not native:
            self._serial_port = '/dev/tty.usbmodem1411';
        else:
            self._serial_port = '/dev/ttyACM0'

        self._comm = None

    def close(self):
        if not self._comm is None:
            self._comm.close()

    def open(self):
        print("%s:%s" % (self._serial_port,self._baud_rate))
        self._comm= serial.Serial(self._serial_port,
                                  self._baud_rate)
        print(self._comm)
        self.flush()
        return True

    def readline(self):
        line_bytes = self._comm.readline()
        line_valid_bytes = bytearray(filter(lambda b: b<128, line_bytes))
        strline = line_valid_bytes.decode('utf-8')
        print(strline)
        return strline

    def reads_available(self):
        return self._comm.in_waiting > 0

    def try_readline(self):
        if self._comm.in_waiting > 0:
            line = self.readline()
        else:
            line = None

        return line

    def writeline(self,string):
        msg = "%s\r\n" % string
        self.write(msg)
        
    def write_newline(self):
        self.write("\r\n")

    def flush(self):
        self._comm.flushInput()
        self._comm.flushOutput()

    def write_bytes(self,byts):
        isinstance(byts,bytearray)
        #nbytes = 0;
        #for i in range(0,len(byts), 32):
        #    nbytes += self._comm.write(byts[i:i+32])
        #    time.sleep(0.1)
        print("writing %d bytes" % len(byts))
        nbytes = self._comm.write(byts)
        print("wrote %d bytes" % nbytes)
        self._comm.flush()

    def write(self,msg):
        self.write_bytes(msg.encode())
'''
    def try_process(self):
        found_process = False
        while True:
            line = self.try_readline()
            if line is None:
                return None
            if "::process::" in line:
                found_process = True

            elif found_process:
                return line


    def process(self):
        while True:
            line = self.readline()

            if "::process::" in line:
                return True


            if not "::listen::" in line:
                print(line)

    def listen(self):
        while True:
            line = self.readline()
            if "::listen::" in line:
                return True

    def synchronize(self):
        data = self.readline()
        if "::wait::" in data:
            print("[[Arduino Due is waiting for input]]")
            input("   Press key when ready:")
            self.writeline('x')
            line = self.readline()
            assert("::recv::" in line)

        elif "::done::" in data:
            print("[[Arduino Due is finished]]")

        else:
            print("[[Arduino Due is desynchronized. Please reprogram device]]")
'''
