
class Command:

    def __init__(self):
        pass

    def pack(self):
        pass

    def unpack(self,bytearr):
        typ = bytearr[0]
        if typ == CmdType.CIRC_CMD:
            return CircCmd.unpack(bytearr[1:])

        elif typ == CmdType.EXPERIMENT_CMD:
            return ExpCmd.unpack(bytearr[1:])
        pass


class ExperimentCommand:

    def __init__(self):
        pass;

    def unpack(self,bytearr):
        typ = bytearr[0]
        print("exp-type %d" % typ)

class CircuitCommand:

    def __init__(self):
        pass;

    def unpack(self,bytearr):
        typ = bytearr[0]
        print("circ-type %d" % typ)
