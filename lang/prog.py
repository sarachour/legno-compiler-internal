
class MathProg:

    def __init__(self):
        self._bindings = {}

    def bind(self,var,expr):
        assert(not var in self._bindings)
        self._bindings[var] = expr

    def bindings(self):
        for var,expr in self._bindings.items():
            yield var,expr
