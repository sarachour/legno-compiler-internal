import ops.op as op
from enum import Enum
import re
from pyparsing import *
import operator
import math

number = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?") \
         .setParseAction(lambda t: float(t[0]))
variable = Word(alphas,alphanums+'_')
operand = number | variable

expop = Literal('^')
signop = oneOf('+ -')
multop = oneOf('* /')
plusop = oneOf('+ -')
factop = Literal('!')

expr = infixNotation( operand,
    [("!", 1, opAssoc.LEFT),
     ("^", 2, opAssoc.RIGHT),
     (signop, 1, opAssoc.RIGHT),
     (multop, 2, opAssoc.LEFT),
     (plusop, 2, opAssoc.LEFT),]
    )

def _build_expr(expr,terms,ctor):
  if len(terms) == 0:
    return expr
  else:
    rhs = build_expr(terms,ctor)
    return ctor(expr,rhs)

def build_expr(exprs,ctor):
  if len(exprs) == 1:
    return exprs[0]
  elif len(exprs) == 0:
    return None
  else:
    return _build_expr(exprs[0],exprs[1:],ctor)

def get_terms(ops,terms,sel_op):
  for op,term in zip(ops,terms):
    if op == sel_op:
      yield term

def negate(expr):
  if expr.op == op.OpType.CONST:
    return op.Const(expr.value*-1)
  else:
    return op.Mult(op.Const(-1), expr)

def from_infix(infix):
  if isinstance(infix,str):
    return op.Var(infix)
  elif isinstance(infix,float):
    return op.Const(infix)
  elif len(infix) == 1:
    return from_infix(infix[0])
  elif len(infix) == 2 and infix[0] == '-':
    return negate(from_infix(infix[1]))

  assert(len(infix) >= 3)
  terms = list(map(lambda i: from_infix(infix[i]), \
              range(0,len(infix),2)))
  ops = [None]+list(map(lambda i: infix[i], \
                        range(1,len(infix),2)))

  if ops[1] == '-' or ops[1] == '+':
    ops[0] = '+'
    sub_terms = list(get_terms(ops,terms,'-'))
    add_terms = list(get_terms(ops,terms,'+'))
    add_expr = build_expr(add_terms,op.Add)
    sub_expr = build_expr(sub_terms,op.Add)

    if len(sub_terms) > 0 and len(add_terms) > 0:
      return op.Add(add_expr,negate(sub_expr))

    elif len(sub_terms) > 0 and len(add_terms) == 0:
      return op.Mult(negate(sub_expr))

    elif len(sub_terms) == 0 and len(add_terms) > 0:
      return add_expr

  elif ops[1] == '*':
    ops[0] = '*'
    return build_expr(terms,op.Mult)
  else:
    raise Exception("unknown: %s" % str(infix))


def parse(strrepr):
  args = ''.join(strrepr.split())
  infix = expr.parseString(args,parseAll=True)
  obj = from_infix(infix)
  return obj
