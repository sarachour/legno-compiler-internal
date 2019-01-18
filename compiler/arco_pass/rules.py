from ops.aop import *

class Rule:

    def __init__(self,name):
        self.name = name

    def group_by(self,group_expr,exprs):
        grouped = {}
        for expr in exprs:
            group = group_expr(expr)
            if not group in grouped:
                grouped[group] = []

            grouped[group].append(expr)

        for group,matches in grouped.items():
            yield group,matches

    def generate_args(self,ast):
        raise NotImplementedError

    def apply_args(self,ast,args):
        raise NotImplementedError

    # test if this transformation is applicable
    def apply(self,ast):
        assert(isinstance(ast,AOp))

        for args in self.generate_args(ast):
            yield self.apply_args(ast,args)



class RReplicateExpr(Rule):

    def __init__(self):
        Rule.__init__(self,"double_expr")

    def apply_args(self,ast,args):
        return ASum([ast]*args)

    def generate_args(self,ast):
        if ast.op == AOp.VAR or ast.op == AOp.SUM:
            yield 2
            yield 3

class RSumGain(Rule):

    def __init__(self):
        Rule.__init__(self,"sum-gain")

    def group_alike(self,expr):
        if expr.op == AOp.CPROD:
            return expr.value,expr.input
        else:
            return 1.0,expr

    def apply_args(self,ast,group_expr):
        inputs = []
        for inp in ast.inputs:
            for const_val,expr,matches in self.group_alike(inp):
                if expr == group_expr:
                    inputs.append(AGain(const_val,Sum([expr]*len(matches))))
                else:
                    inputs.append(inp)

        return Sum(inputs)

    def generate_args(self,ast):
        if ast.op != AOp.SUM:
            return

        groups = list(filter(lambda group: len(group[1]) > 1,
                        self.group_by(self.group_alike,ast.inputs)))

        if len(groups) == 0:
            return

        for (_,expr),_ in groups:
            yield expr

def get_rules():
    rules = []
    #rules.append(RSumGain())
    #rules.append(RReplicateExpr())
    return rules
