#
# Built-in Functions
#

from lisp import *
import __main__

class BuiltinError(LispError): pass


# Basics
#
def builtin_atom(x):
    if x.is_atom():
        return LispTrue()
    else:
        return LispList()

def builtin_eq(a, b):
    if a == b:
        return LispTrue()
    else:
        return LispList()

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

    if x < y:
        return LispTrue()
    else:
        return LispList()

def builtin_le(x, y):
    if type(x) != LispInt or type(y) != LispInt:
        raise BuiltinError('builtin_lt: illegal parameter type')

    if x <= y:
        return LispTrue()
    else:
        return LispList()


def builtin_gt(x, y):
    if type(x) != LispInt or type(y) != LispInt:
        raise BuiltinError('builtin_gt: illegal parameter type')

    if x > y:
        return LispTrue()
    else:
        return LispList()

def builtin_ge(x, y):
    if type(x) != LispInt or type(y) != LispInt:
        raise BuiltinError('builtin_gt: illegal parameter type')

    if x >= y:
        return LispTrue()
    else:
        return LispList()


# Bool
#
def builtin_not(x):
    if not x.is_true():
        return LispTrue()
    else:
        return LispList()

def builtin_and(x, y):
    if x.is_true() and y.is_true():
        return LispTrue()
    else:
        return LispList()

def builtin_or(x, y):
    if x.is_true() or y.is_true():
        return LispTrue()
    else:
        return LispList()


# Input / Output
#
def builtin_print(*param):
    for p in param:
        print(p, end='')
    return LispList()

def builtin_println(*param):
    builtin_print(*param)
    print()
    return LispList()


TABLE = {
        LispSym('head') : LispBuiltin(builtin_head, 1),
        LispSym('tail') : LispBuiltin(builtin_tail, 1),
        LispSym('print') : LispBuiltin(builtin_print, None),
        LispSym('println') : LispBuiltin(builtin_println, None),
        LispSym('cons') : LispBuiltin(builtin_cons, 2),
        LispSym('atom') : LispBuiltin(builtin_atom, 1),
        LispSym('list') : LispBuiltin(builtin_list),
        LispSym('eval') : LispBuiltin(builtin_eval, 1),
        LispSym('eq') : LispBuiltin(builtin_eq, 2),
        LispSym('lt') : LispBuiltin(builtin_lt, 2),
        LispSym('le') : LispBuiltin(builtin_le, 2),
        LispSym('gt') : LispBuiltin(builtin_gt, 2),
        LispSym('ge') : LispBuiltin(builtin_ge, 2),
        LispSym('+') : LispBuiltin(builtin_add, 2),
        LispSym('-') : LispBuiltin(builtin_sub, 2),
        LispSym('*') : LispBuiltin(builtin_mul, 2),
        LispSym('/') : LispBuiltin(builtin_div, 2),
        LispSym('mod') : LispBuiltin(builtin_mod, 2),
        LispSym('not') : LispBuiltin(builtin_not, 1),
        LispSym('and') : LispBuiltin(builtin_and, 2),
        LispSym('or') : LispBuiltin(builtin_or, 2),
    }

