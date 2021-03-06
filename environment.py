#
# eval functions
#

import parser
import builtin

from lisp import *

class EvalError(LispError): pass


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
                function = LispList([ LispSym("lambda"),
                                      lambda_parameter,
                                      lambda_body ])
                value = LispLambda(function)
                self.symbols[symbol] = value

                return value

            if cmd == "symbols":
                return LispList(self.symbols)


        if interactive:
            return self.evaluate(instruction)

        raise EvalError("illegal instruction: %s" % (instruction))




    def evaluate(self, expr, stack = None, bindings = 0):
        if stack is None:
            stack = []

        while True:
            #print("eval: %s  stack: %s  bindings: %d" % (expr, stack, bindings))

            if expr.is_atom():
                if type(expr) == LispSym:
                    if expr in self.symbols:
                        return self.symbols[expr]
                    raise EvalError("%s: unknown symbol" % (expr))

                if type(expr) == LispRef:
                    return stack[-int(expr)]

                if type(expr) == LispLambda:
                    return expr

                if type(expr) == LispClosure:
                    return expr.capture(stack)

                return expr


            function = expr.head()
            parameter = expr.tail()

            if type(function) == LispSym:
                if   function == 'quote':
                    if len(parameter) != 1:
                        raise EvalError('quote expects exactly one parameter')

                    return parameter[0]

                elif function == 'if':
                    if len(parameter) != 3:
                        raise EvalError('if expects exactly 3 parameters')

                    if self.evaluate(parameter[0], stack).is_true():
                        expr = parameter[1]
                    else:
                        expr = parameter[2]
                    continue

                elif function == 'eval':
                    if len(parameter) != 1:
                        raise EvalError('eval expects exactly one parameter')

                    expr = self.evaluate(parameter[0], stack)
                    continue

                elif function == 'lambda':
                    return LispLambda(expr)


            evalpar = [ self.evaluate(p, stack) for p in parameter ]
            evalfun = self.evaluate(function, stack)

            if type(evalfun) == LispBuiltin:
                if evalfun.argc is not None and evalfun.argc != len(evalpar):
                    raise EvalError("%s: expects %d parameter, got %d"
                            % (function, evalfun.argc, len(evalpar)))

                try:
                    return evalfun.function(*evalpar)
                except TypeError:
                    raise EvalError("%s: illegal number of parameter to builtin function"
                            % (function))

            if isinstance(evalfun, LispLambda):
                if evalfun.argc != len(evalpar):
                    raise EvalError("%s: expects %d parameter, got %d" %
                            (function, evalfun.argc, len(evalpar)))

                #print("[DEBUG] evalfun: %s, evalpar: %s, function: %s" % (evalfun, evalpar, function))

                # check if we are executing an explicit lisp-lambda instead of an
                # indirect one via symbol or call result. In case of a direct
                # lambda, we are not allowed to clear current bindings, because
                # it's body might still refer to them.
                if type(function) != LispLambda and bindings > 0:
                    stack = stack[:-bindings]
                    bindings = 0

                # add evaluated parameters to stack as new bindings
                stack = stack + evalpar
                bindings += len(evalpar)

                # if we execute a closure, add captured values to stack
                if type(evalfun) == LispClosure:
                    stack = stack + evalfun.capture_values
                    bindings += len(evalfun.capture_values)

                expr = evalfun.body
                continue

            raise EvalError("%s: not executable" % (evalfun))
