#
# Built-in Functions
#

from lisp import *
import __main__

class BuiltinError(LispError): pass


# Basics
#
def builtin_atom(x):
    return x.is_atom()

def builtin_eq(a, b):
    return a == b

def builtin_head(L):
    if L.is_atom():
        raise BuiltinError("head: non-empty list expected")

    return L.head()

def builtin_tail(L):
    if L.is_atom():
        raise BuiltinError("tail: non-empty list expected")

    return L.tail()

def builtin_cons(x, L):
    if type(L) != LispList:
        raise BuiltinError('cons: list expected as second parameter')

    return LispList([x] + L)

def builtin_list(*L):
    return LispList(L)

def builtin_quote(x):
    return x

def builtin_eval(x):
    # evaluate in main environment - this is a bit ugly
    return __main__.env.evaluate(x)


# Arithmetic
#
def builtin_add(x, y):
    if type(x) != LispInt or type(y) != LispInt:
        raise BuiltinError('builtin_add: illegal parameter type')

    return LispInt(x + y)

def builtin_sub(x, y):
    if type(x) != LispInt or type(y) != LispInt:
        raise BuiltinError('builtin_sub: illegal parameter type')

    return LispInt(x - y)


def builtin_mul(x, y):
    if type(x) != LispInt or type(y) != LispInt:
        raise BuiltinError('builtin_mul: illegal parameter type')

    return LispInt(x * y)

def builtin_div(x, y):
    if type(x) != LispInt or type(y) != LispInt:
        raise BuiltinError('builtin_div: illegal parameter type')

    if y == 0:
        raise BuiltinError('builtin_div: divide by zero')

    return LispInt(x // y)


def builtin_mod(x, n):
    if type(x) != LispInt or type(n) != LispInt:
        raise BuiltinError('builtin_mod: illegal parameter type')

    return LispInt(x % n)


def builtin_lt(x, y):
    if type(x) != LispInt or type(y) != LispInt:
        raise BuiltinError('builtin_lt: illegal parameter type')

    return LispInt(x < y)


def builtin_gt(x, y):
    if type(x) != LispInt or type(y) != LispInt:
        raise BuiltinError('builtin_gt: illegal parameter type')

    return LispInt(x > y)


# Input / Output
#
def builtin_print(*param):
    for p in param:
        print(p, end='')
    return NIL

def builtin_println(*param):
    builtin_print(*param)
    print()
    return NIL


TABLE = {
        'head' : LispBuiltin(builtin_head, 1),
        'tail' : LispBuiltin(builtin_tail, 1),
        'print' : LispBuiltin(builtin_print, None, side=True),
        'println' : LispBuiltin(builtin_println, None, side=True),
        'cons' : LispBuiltin(builtin_cons, 2),
        'atom' : LispBuiltin(builtin_atom, 1),
        'quote' : LispBuiltin(builtin_quote, 1),
        'eval' : LispBuiltin(builtin_eval, 1),
        #'eq' : LispBuiltin(builtin_eq, 2),
        #'list' : LispBuiltin(builtin_list),
        #'mod' : LispBuiltin(builtin_mod, 2),
        #'lt' : LispBuiltin(builtin_lt, 2),
        #'gt' : LispBuiltin(builtin_gt, 2),
        '+' : LispBuiltin(builtin_add, 2),
        #'-' : LispBuiltin(builtin_sub, 2),
        #'*' : LispBuiltin(builtin_mul, 2),
        #'/' : LispBuiltin(builtin_div, 2),
    }

