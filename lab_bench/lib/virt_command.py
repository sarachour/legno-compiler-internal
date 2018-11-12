from lib.base_command import Command

class SetReferenceFunction(Command):

    def __init__(self,pyexpr):
        Command.__init__(self)
        self.pyexpr = pyexpr

    @staticmethod
    def name():
        return 'set_ref_func'


    @staticmethod
    def desc():
        return "set the reference function."


    @staticmethod
    def parse(args):
        def usage():
            print("set_ref_func <expr(t)>")

        if len(args) < 1:
            usage()
            return None

        expr = " ".join(args[0:])
        return SetReferenceFunction(expr)


    def execute(self,state):
        state.ref_func = self.pyexpr
