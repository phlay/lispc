#
# eval functions
#

import parser
import builtin

from lisp import *

class EvalError(LispError): pass
class EvalNoValue(EvalError): pass



def local_sym_to_ref(sym, local):
    n = len(local)
    for i in range(n):
        if sym == local[n - i - 1]:
            return LispRef(i+1)
    return None



class Environment:

    def __init__(self, symbols = None):
        if symbols is None:
            symbols = builtin.TABLE

        self.symbols = symbols.copy()


    #
    # file loading
    #
    def import_file(self, fn):
        with open(fn, "r") as f:
            lisp_file = parser.file_parser.parse(f.read())

        for item in lisp_file:
            self.interpret(item)


    #
    # interpret
    #
    def interpret_single_line(self, line):
        return self.interpret(parser.line_parser.parse(line), True)

    def interpret(self, instruction, interactive = False):
        if not instruction.is_atom() and type(instruction[0]) == LispSym:
            cmd = instruction.head()
            parameter = instruction.tail()

            if cmd == "set":
                if len(parameter) != 2:
                    raise EvalError("set expects exactly two parameter")
                if type(parameter[0]) != LispSym:
                    raise EvalError("set expects symbol as first parameter")

                value = self.evaluate(parameter[1])

                self.symbols[parameter[0]] = value

                return value

            if cmd == "defun":
                if len(parameter) != 3:
                    raise EvalError("defun expects three parameter")

                symbol = parameter[0]
                lambda_parameter = parameter[1]
                lambda_body = parameter[2]

                if type(symbol) != LispSym:
                    raise EvalError("defun expects symbol as first parameter")
                if type(lambda_parameter) != LispList:
                    raise EvalError("defun expects list of symbols as second parameter")

                # construct lambda
                function = LispList([ LispSym("lambda"), lambda_parameter, lambda_body ])

                self.symbols[symbol] = function

                value = self.bake_lambda(function[1:])

                self.symbols[symbol] = value

                return value

        if interactive:
            return self.evaluate(instruction)

        raise EvalError("illegal instruction: %s" % (instruction))





    #
    # evaluate
    #

    def evaluate(self, expr, stack = None, local = None):
        if stack is None:
            stack = []
        if local is None:
            local = []

        if expr.is_atom():
            if type(expr) == LispSym:
                if local_sym_to_ref(expr, local):
                    raise EvalNoValue("local variable has no value")
                if expr in self.symbols:
                    return self.symbols[expr]
                raise EvalNoValue("unknown symbol: %s" % (expr))

            if type(expr) == LispRef:
                if int(expr) <= len(local):
                    raise EvalNoValue("local reference has no value")
                return stack[len(local)-int(expr)]

            return expr


        function = expr.head()
        parameter = expr.tail()

        if type(function) == LispSym:
            if   function == 'quote':
                if len(parameter) != 1:
                    raise EvalError('quote expects exactly one parameter')

                return parameter[0]
            elif function == 'if':
                return self.eval_if(parameter, stack, local)
            elif function == 'eval':
                return self.eval_eval(parameter, stack, local)
            elif function == 'lambda':
                return self.bake_lambda(parameter, stack, local)
            elif function == 'λ':
                return self.bake_closure(parameter, stack, local)

        evalfun = self.evaluate(function, stack, local)
        evalpar = [ self.evaluate(p, stack, local) for p in parameter ]

        if type(evalfun) == LispBuiltin:
            if evalfun.argc is not None and evalfun.argc != len(evalpar):
                raise EvalError("%s: expects %d parameter, got %d" % (function, evalfun.argc, len(evalpar)))

            try:
                return evalfun.function(*evalpar)
            except TypeError:
                raise EvalError("%s: illegal number of parameter to builtin function" % (function))

        elif evalfun.is_head("λ"):
            if evalfun[1] != len(evalpar):
                raise EvalError("%s: expects %d parameter, got %d" % (function, evalfun[1], len(evalpar)))

            return self.eval_apply_lambda(evalfun, evalpar, stack, local)

        else:
            raise EvalError("list is not executeable: %s" % (evalfun))


    def eval_if(self, parameter, stack, local):
        if len(parameter) != 3:
            raise EvalError('if expects exactly 3 parameters')

        if self.evaluate(parameter[0], stack, local):
            return self.evaluate(parameter[1], stack, local)
        else:
            return self.evaluate(parameter[2], stack, local)


    def eval_eval(self, parameter, stack, local):
        if len(parameter) != 1:
            raise EvalError('eval expects exactly one parameter')

        return self.evaluate(self.evaluate(parameter[0], stack, local), stack, local)



    def eval_apply_lambda(self, function, parameter, stack, local):
        lambda_argc = function[1]
        lambda_body = function[2]

        if len(parameter) != lambda_argc:
            raise EvalError("lambda needs %d parameter but got %d" % (lambda_argc, len(parameter)))

        return self.evaluate(lambda_body, stack + [None] + parameter, local)




    #
    # Baking lambdas: (lambda (x1 x2 ... xk) body) -> (λ k newbody)
    # where new body uses $1, ..., $k instead of xk, ..., x1
    #

    def bake_lambda(self, parameter, stack = None, local = None):
        if stack is None:
            stack = []
        if local is None:
            local = []

        lambda_parameter = parameter[0]
        lambda_body = parameter[1]

        compiled_body = self.bake_expr(lambda_body, stack, local + [""] + lambda_parameter)

        return LispList( [LispSym("λ"), len(lambda_parameter), compiled_body] )


    def bake_closure(self, parameter, stack = None, local = None):
        if stack is None:
            stack = []
        if local is None:
            local = []

        lambda_argc = parameter[0]
        lambda_body = parameter[1]

        # recompile lambda with dummy parameter on local symbol table
        compiled_body = self.bake_expr(lambda_body, stack, local + (lambda_argc+1)*[''])

        return LispList( [LispSym("λ"), lambda_argc, compiled_body] )


    def bake_expr(self, expr, stack, local):
        if expr.is_atom():
            if type(expr) == LispSym:
                local_ref = local_sym_to_ref(expr, local)
                if local_ref is not None:
                    return local_ref

                return expr

            if type(expr) == LispRef:
                if int(expr) <= len(local):
                    return expr
                return stack[len(local)-int(expr)]

            return expr


        function = expr.head()
        parameter = expr.tail()

        if type(function) == LispSym:
            if function == "quote":
                if len(parameter) != 1:
                    raise EvalError("quote needs exactly one parameter")
                return expr
            elif function == "if":
                return self.bake_if(parameter, stack, local)
            elif function == "lambda":
                return self.bake_lambda(parameter, stack, local)
            elif function == "λ":
                return self.bake_closure(parameter, stack, local)

        # compile function call

        # XXX optimization disabled for now
        #try:
        #    return self.evaluate(expr, stack, local)
        #except EvalNoValue:
        #    pass

        compiled_expr = LispList([ self.bake_expr(p, stack, local) for p in expr ])
        compiled_function = compiled_expr.head()

        if not compiled_function.is_executeable():
            raise EvalError("function is not executable: %s" % (compiled_function))

        return compiled_expr


    def bake_if(self, parameter, stack, local):
        if len(parameter) != 3:
            raise EvalError("if needs exactly three parameter")

        # try evaluate condition
        condition = parameter[0]
        case_true = self.bake_expr(parameter[1], stack, local)
        case_false = self.bake_expr(parameter[2], stack, local)

        # XXX optimization disabled for now
        #if not condition.is_head('quote'):
        #    try:
        #        if self.evaluate(condition, stack, local).is_true():
        #            return case_true
        #        else:
        #            return case_false
        #    except EvalNoValue:
        #        pass

        # direct evaluation did not work out, compile conditional instead
        condition = self.bake_expr(condition, stack, local)

        return LispList([ LispSym("if"), condition, case_true, case_false ])
