import lib.cstructs as cstructs
import time
import lib.enums as enums
from enum import Enum
import re

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


    def execute(self,state,kwargs={}):
        if self._success:
            return self.execute_command(state,**kwargs)
        else:
            print("[error]" % self._msg)

        return None

    def tostr(self):
        raise NotImplementedError

class ArduinoResponseType(Enum):
    LISTEN = "listen"
    PROCESS = "process"
    DEBUG = "debug"
    DONE = "done"
    DATA = "data"
    ERROR = "error"
    PAYLOAD = "array"
    MESSAGE = "msg"
    RESPONSE = "resp"

class ArduinoResponseState(Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    WAITFOR_DATA = "waitfor-data"
    WAITFOR_PAYLOAD = "waitfor-payload"


class ArduinoResponseDataType(Enum):
    FLOAT = "f"
    FLOATARRAY = "F"
    INT = "i"


class GenericArduinoResponse:

    def __init__(self,type_):
        self._type = type_

    @property
    def type(self):
        return self._type

    def __repr__(self):
        return "generic-resp(%s)" % self.type.value

class MessageArduinoResponse(GenericArduinoResponse):

    def __init__(self,msg):
        GenericArduinoResponse.__init__(self,ArduinoResponseType.MESSAGE)
        self._msg = msg

    @property
    def message(self):
        return self._msg

    def __repr__(self):
        return "message-resp(%s)" % \
            (self._msg)

    @staticmethod
    def parse(args):
        msg = args[0]
        return MessageArduinoResponse(msg)



class HeaderArduinoResponse(GenericArduinoResponse):

    def __init__(self,msg,n_args):
        GenericArduinoResponse.__init__(self,ArduinoResponseType.RESPONSE)
        self._msg = msg
        self._n = n_args
        self._args = [None]*n_args

    def done(self):
        for arg in self._args:
            if arg is None:
                return False
        return True

    def set_data(self,idx,arg):
        assert(idx < self._n)
        self._args[idx] = arg

    @property
    def message(self):
        return self._msg

    def data(self,i):
        return self._args[i]

    @staticmethod
    def parse(args):
        n = int(args[0])
        msg = args[1]
        return HeaderArduinoResponse(msg,n)

    def __repr__(self):
        return "header-resp(%s,%d) {%s}" % \
            (self._msg,self._n,self._args)

class DataArduinoResponse(GenericArduinoResponse):

    def __init__(self,value,size=1):
        GenericArduinoResponse.__init__(self,ArduinoResponseType.DATA)
        self._value = value
        self._size = size

    @property
    def value(self):
        return self._value

    def set_value(self,v):
        self._value = v

    def is_array(self):
        return self._size > 1

    @staticmethod
    def parse(args):
        typ = args[0]
        print("data",args)
        if typ == 'i':
            return DataArduinoResponse(int(args[1]))
        elif typ == 'f':
            return DataArduinoResponse(float(args[1]))
        elif typ == 'F':
            return DataArduinoResponse(None,size=int(args[1]))
        else:
            raise Exception("unimpl")



class PayloadArduinoResponse(GenericArduinoResponse):

    def __init__(self,n):
        GenericArduinoResponse.__init__(self,ArduinoResponseType.PAYLOAD)
        self._array = None
        self._n = n


    def set_array(self,data):
        assert(len(data) == self._n)
        self._array = data

    @staticmethod
    def parse(args):
        print(args)
        raise Exception("unimpl")


class ArduinoCommand(Command):
    HEADER = "AC:>"
    # 1=only print commands
    # 0=run commands
    #DEBUG = 0
    DEBUG = 0


    def __init__(self,typ=cstructs.cmd_t()):
        Command.__init__(self)
        self._c_type = typ

    def build_dtype(self,rawbuf):
        raise NotImplementedError

    def build_ctype(self):
        raise NotImplementedError


    @staticmethod
    def parse_response(msg):
        rest = msg.strip().split(ArduinoCommand.HEADER)[1]
        args = list(filter(lambda tok: len(tok) > 0, \
                           re.split("[\]\[]+",rest)))
        typ = ArduinoResponseType(args[0])
        if typ == ArduinoResponseType.RESPONSE:
            return HeaderArduinoResponse.parse(args[1:])

        if typ == ArduinoResponseType.MESSAGE:
            return MessageArduinoResponse.parse(args[1:])

        elif typ == ArduinoResponseType.DATA:
            return DataArduinoResponse.parse(args[1:])

        elif typ == ArduinoResponseType.PAYLOAD:
            return PayloadArduinoResponse.parse(args[1:])

        else:
            return GenericArduinoResponse(typ)

    @staticmethod
    def is_response(msg):
        return msg.startswith(ArduinoCommand.HEADER)

    def get_response(self,st):
        ard = st.arduino
        state = ArduinoResponseState.PENDING
        this_resp = None
        this_data = None
        data_idx = 0

        while True:
            line = ard.readline()
            if self.is_response(line):
                resp = self.parse_response(line)
                if resp.type == ArduinoResponseType.LISTEN:
                    assert(state == ArduinoResponseState.PENDING)
                    continue

                if resp.type == ArduinoResponseType.PROCESS:
                    assert(state == ArduinoResponseState.PENDING)
                    state = ArduinoResponseState.PROCESSED

                elif resp.type == ArduinoResponseType.RESPONSE:
                    assert(state == ArduinoResponseState.PROCESSED)
                    state = ArduinoResponseState.WAITFOR_DATA
                    this_resp = resp
                    if this_resp.done():
                        return this_resp

                elif resp.type == ArduinoResponseType.DATA:
                    if resp.is_array():
                        this_data = resp
                        state = ArduinoResponseState.WAITFOR_PAYLOAD
                    else:
                        this_resp.set_data(data_idx, resp.value)
                        data_idx += 1

                    if this_resp.done():
                        return this_resp

                elif resp.type == ArduinoResponseType.PAYLOAD:
                    assert(state == ArduinoResponseState.WAITFOR_PAYLOAD)
                    this_data.set_value(resp.array)
                    this_resp.set_data(data_idx, this_data.value)
                    data_idx += 1
                    this_data = None
                    state = ArduinoResponseState.WAITFOR_DATA

                    if this_resp.done():
                        return this_resp

                elif resp.type == ArduinoResponseType.MESSAGE:
                    print(resp.message)

                elif resp.type == ArduinoResponseType.DONE:
                    print("<simulation finished>")
                    continue

                elif resp.type == ArduinoResponseType.ERROR:
                    raise Exception(resp.message)

                else:
                    raise Exception("unhandled: %s" % line)


    def try_waitfor(self,st,type_):
        ard = st.arduino
        while True:
            line = ard.try_readline()
            #print("try_waitfor[%s]> %s" % (type_.value,line))
            if line is None:
                return False

            if self.is_response(line):
                resp = self.parse_response(line)
                if resp.type == type_:
                    return True

    def waitfor(self,st,type_):
        ard = st.arduino
        while True:
            line = ard.readline()
            #print("waitfor[%s]> %s" % (type_.value,line))
            if self.is_response(line):
                resp = self.parse_response(line)
                if resp.type == type_:
                    return True


    def write_to_arduino(self,state,cdata):
        if not state.dummy:
            #print("execute: %s [%d]" % (self,len(cdata)))
            # twenty bytes
            self.waitfor(state,ArduinoResponseType.LISTEN)
            state.arduino.write_bytes(cdata)
            state.arduino.write_newline()
            return self.get_response(state)

        return None

    def execute_command(self,state,raw_data=None):
        if state.dummy:
            return None

        header_type= self.build_ctype()
        header_data = self._c_type.build(header_type)
        if not raw_data is None:
            body_type = self.build_dtype(raw_data)
            body_data = data_type.build(raw_data)
            rawbuf = header_data + body_data

        else:
            rawbuf = header_data

        rep = ""
        for byt in rawbuf:
            rep += str(int(byt)) + " "

        print("cmd:> %s" % rep)
        resp = self.write_to_arduino(state,rawbuf)
        print("resp:> %s" % resp)
        return resp

        return None

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

    def execute_command(self,state):
        ArduinoCommand.execute_command(self,state)
        return True

    def __repr__(self):
        return "flush"
