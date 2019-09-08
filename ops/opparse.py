import ops.op as op
from enum import Enum
import re
#from pyparsing import *
#import operator
import math
import lark

GRAMMAR = '''
?start: sum
    ?sum: product
        | sum "+" product   -> add
        | sum "-" product   -> sub
    ?product: atom
        | product "*" atom  -> mul
    ?atoms: atom
         | atoms "," atom -> lst
    ?atom: NUMBER           -> number
         | "-" atom         -> neg
         | NAME             -> var
         | NAME "(" atoms ")"      -> func
         | "(" sum ")"
    %import common.CNAME -> NAME
    %import common.NUMBER
    %import common.WS_INLINE
    %ignore WS_INLINE
'''

PARSER = lark.Lark(GRAMMAR)

def report(clause,msg):
  if not clause:
    raise Exception("when parsing <%s> : %s" % (node,msg))

def function_to_dslang_ast(dsprog,name,arguments):
  n = len(arguments)
  if dsprog.has_lambda(name):
    freevars,impl = dsprog.lambda_spec(name);
    report(len(freevars) == n, \
           "expected <%d> args, got <%d>" % (len(freevars),n))
    return op.Call(arguments, \
                   op.Func(freevars, impl));
  elif name == "sin":
    report(n == 1, "expected 1 argument to sin function")
    return op.Sin(arguments[0])
  elif name == "sgn":
    report(n == 1, "expected 1 argument to sgn function")
    return op.Sgn(arguments[0])
  elif name == "sqrt":
    report(n == 1, "expected 1 argument to sqrt function")
    return op.Sqrt(arguments[0])
  elif name == "abs":
    report(n == 1, "expected 1 argument to abs function")
    return op.Abs(arguments[0])

  else:
    raise Exception("unknown built-in function <%s>" % name)


def lark_to_dslang_ast(dsprog,node):
  def recurse(ch):
    return lark_to_dslang_ast(dsprog,ch)

  n = len(node.children)
  if node.data == "neg":
    report(n == 1, "negation operation takes one argument");
    expr = recurse(node.children[0])
    if(expr.op == op.OpType.CONST):
        return op.Const(-1*expr.value);
    else:
        return op.Mult(op.Const(-1),expr)

  if node.data == "func":
    report(n > 0, "function name not specified");
    func_name = node.children[0]
    report(func_name.type == "NAME", "expected Token.NAME");
    arguments = list(map(lambda ch: recurse(ch), node.children[1:]))
    return function_to_dslang_ast(dsprog,func_name.value,arguments);

  if node.data == "number":
    number = node.children[0]
    report(number.type == "NUMBER", "expected Token.NUMBER");
    value = float(number.value)
    return op.Const(value)

  if node.data == "var":
    report(n == 1, "variable must have token");
    var_name = node.children[0]
    report(var_name.type == "NAME", "expected Token.NAME");
    return op.Var(var_name.value)

  if node.data == "sub":
    report(n == 2, "only binary subtraction are supported");
    e1 = recurse(node.children[0])
    e2 = recurse(node.children[1])
    return op.Add(e1,op.Mult(op.Const(-1),e2))


  if node.data == "add":
    report(n == 2, "only binary adds are supported");
    e1 = recurse(node.children[0])
    e2 = recurse(node.children[1])
    return op.Add(e1,e2)

  if node.data == "mul":
    report(n == 2, "only binary mults are supported");
    e1 = recurse(node.children[0])
    e2 = recurse(node.children[1])
    return op.Mult(e1,e2)

  else:
    raise Exception("???")


def parse(dsprog,strrepr):
  lark_ast = PARSER.parse(strrepr)
  obj = lark_to_dslang_ast(dsprog,lark_ast)
  return obj
