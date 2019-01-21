import ops.op as op
from enum import Enum
import re
from pyparsing import *
import operator
import math

number = Regex(r"[+-]?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?") \
         .setParseAction(lambda t: float(t[0]))
variable = Word(alphas)
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

def from_infix(infix):
  if isinstance(infix,str):
    return op.Var(infix)
  elif isinstance(infix,float):
    return op.Const(infix)
  elif len(infix) == 1:
    return from_infix(infix[0])

  assert(len(infix) >= 3)
  lhs = from_infix(infix[0])
  rhs = from_infix(infix[2:])
  assert(isinstance(lhs,op.Op))
  assert(isinstance(rhs,op.Op))
  this_op = infix[1]
  if this_op == '*':
    return op.Mult(lhs,rhs)
  elif this_op == '-':
    return op.Add(lhs,op.Mult(op.Const(-1),rhs))
  elif this_op == '+':
    return op.Add(lhs,rhs)
  else:
    raise Exception("unknown: %s" % str(infix))

def parse(strrepr):
  args = ''.join(strrepr.split())
  infix = expr.parseString(args,parseAll=True)
  obj = from_infix(infix)
  return obj
