import serial
class ArduinoDue:

    def __init__(self,native=True):
        self._baud_rate = 115200
        if not native:
            self._serial_port = '/dev/tty.usbmodem1411';
        else:
            self._serial_port = 'dev/ttyACM0'

        self._comm = None

    def close(self):
        if not self._comm is None:
            self._comm.close()

    def open(self):
        print("%s:%s" % (self._serial_port,self._baud_rate))
        self._comm= serial.Serial(self._serial_port, self._baud_rate)
        self._comm.flushInput()
        self._comm.flushOutput()
        return True

    def readline(self):
        line_bytes = self._comm.readline()
        return line_bytes.decode('utf-8')

    def try_readline(self):
        if self._comm.in_waiting > 0:
            line = self.readline()
        else:
            line = None

        return line

    def writeline(self,string):
        msg = "%s\r\n" % string
        self.write(msg)

    def write_bytes(self,byts):
        isinstance(byts,bytearray)
        self._comm.write(byts)

    def write(self,msg):
        self._comm.write(msg.encode())

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
