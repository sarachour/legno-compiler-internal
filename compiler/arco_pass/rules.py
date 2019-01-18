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


class RNegateFanout(Rule):

    def __init__(self,board):
        Rule.__init__(self,"negate_fanout")
        coeffs = []
        block = board.block('fanout')
        for mode in block.comp_modes:
            for _,expr in block.dynamics(mode):
                coeffs.append(expr.coefficient())

        self._opts = set(coeffs)

    def generate_args(self,ast):
        if ast.op == AOpType.CPROD and \
           ast.value in self._opts:
            if ast.input.op == AOpType.VAR:
                yield 1
            elif ast.input.op == AOpType.VPROD:
                for idx,inp in enumerate(ast.input.inputs):
                    if inp.op == AOpType.VAR:
                        yield idx

    def apply_args(self,ast,term_idx):
        if ast.input.op == AOpType.VAR:
            return AVar(ast.input.name, ast.value)

        if ast.input.op == AOpType.VPROD:
            new_args = []
            for idx,inp in enumerate(ast.input.inputs):
                if idx == term_idx:
                    new_args.append(AVar(inp.name,ast.value))
                else:
                    new_args.append(inp)
            return AProd(new_args)


        raise Exception("unhandled: %s" % ast)

def get_rules(board):
    rules = []
    rules.append(RNegateFanout(board))
    return rules
