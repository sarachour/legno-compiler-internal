import lib.cstructs as cstructs
import time
import lib.enums as enums

class OptionalValue:

    def __init__(self,value,success=True):
        self.value = value
        self.success = success

    @property
    def message(self):
        assert(not self.success)
        return self.value

    @staticmethod
    def error(msg):
        return OptionalValue(msg,success=False)

    @staticmethod
    def value(val):
        return OptionalValue(val,success=True)

class Command:
    # debug =1 : don't run me
    def __init__(self):
        self._success = True
        self._msg = None

    def fail(self,msg):
        self._msg = msg
        self._success = False

    def test(self):
        return self._success

    def error_msg(self):
        return self._msg

    def process_response(self,resp):
        return resp

    def execute(self,state):
        if self._success:
            resp = self.execute_command(state)
            if not resp is None:
                return self.process_response(resp)
        else:
            print("[error]" % self._msg)

        return None

    def tostr(self):
        raise NotImplementedError

class ArduinoCommand(Command):
    # 1=only print commands
    # 0=run commands
    DEBUG = 0

    def __init__(self,typ=cstructs.cmd_t()):
        Command.__init__(self)
        self._c_type = typ

    def build_ctype(self):
        raise NotImplementedError

    def write_to_arduino(self,state,cdata):
        if not state.dummy:
            print("execute: %s [%d]" % (self,len(cdata)))
            # twenty bytes
            state.arduino.listen()
            state.arduino.write_bytes(cdata)
            state.arduino.write_newline()
            state.arduino.process()
            return state.arduino.readline()

        return None

    def execute_command(self,state):
        data = self.build_ctype()
        cdata = self._c_type.build(data)
        rep = ""
        for byt in cdata:
            rep += str(int(byt)) + " "
        #print("bytes: %s" % rep)
        resp = self.write_to_arduino(state,cdata)
        #print("resp:> %s" % resp)
        return resp

class FlushCommand(ArduinoCommand):
    def __init__(self):
        ArduinoCommand.__init__(self);

    def build_ctype(self):
        return {
            'test':ArduinoCommand.DEBUG,
            'type':enums.CmdType.FLUSH_CMD.name,
            'data': {
                'flush_cmd':255
            }
        }


    def write_to_arduino(self,state,cdata):
        if not state.dummy:
            #print("execute: %s [%d]" % (self,len(cdata)))
            # twenty bytes
            found_process = False
            while True:
                state.arduino.listen()
                state.arduino.write_bytes(cdata)
                state.arduino.write_newline()
                time.sleep(0.5)
                if state.arduino.reads_available():
                    line = state.arduino.try_process()
                    if not line is None:
                        return line

        return None


    def process_response(self,resp):
        #print("resp:> %s" % resp)
        if not resp is None and \
           "::flush::" in resp:
            return True
        return False

    def __repr__(self):
        return "flush"
