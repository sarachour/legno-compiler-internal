import lib.cstructs as cstructs

class Command:

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

    def execute(self,state):
        if self._success:
            self.execute_command(state)
        else:
            print("[error]" % self._msg)
            return

    def tostr(self):
        raise NotImplementedError

class ArduinoCommand(Command):

    def __init__(self,typ=cstructs.cmd_t()):
        Command.__init__(self)
        self._c_type = typ
        self.dummy = True

    def build_ctype(self):
        raise NotImplementedError

    def write_to_arduino(self,state,cdata):
        if not state.dummy:
            state.arduino.write(cdata)

    def execute_command(self,state):
        print(self)
        data = self.build_ctype()
        cdata = self._c_type.build(data)
        self.write_to_arduino(state,cdata)
