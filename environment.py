#
# eval functions
#

import parser
import builtin

from lisp import *

class EvalError(LispError): pass
class EvalNoValue(EvalError): pass


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




    def evaluate(self, expr, stack = None, argc = 0):
        if stack is None:
            stack = []

        while True:
            if expr.is_atom():
                if type(expr) == LispSym:
                    if expr in self.symbols:
                        return self.symbols[expr]
                    raise EvalNoValue("unknown symbol: %s" % (expr))

                if type(expr) == LispRef:
                    return stack[-int(expr)]

                if type(expr) == LispLambda:
                    return expr.closure(stack)

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


            evalfun = self.evaluate(function, stack)
            evalpar = [ self.evaluate(p, stack) for p in parameter ]

            if type(evalfun) == LispBuiltin:
                if evalfun.argc is not None and evalfun.argc != len(evalpar):
                    raise EvalError("%s: expects %d parameter, got %d"
                            % (function, evalfun.argc, len(evalpar)))

                try:
                    return evalfun.function(*evalpar)
                except TypeError:
                    raise EvalError("%s: illegal number of parameter to builtin function"
                            % (function))

            if type(evalfun) == LispLambda:
                if evalfun.argc != len(evalpar):
                    raise EvalError("%s: expects %d parameter, got %d" %
                            (function, evalfun.argc, len(evalpar)))

                if argc > 0:
                    stack = stack[:-argc]

                newframe = evalfun.stack + [LispList()] + evalpar
                stack += newframe
                argc = len(newframe)
                expr = evalfun.body
                continue


            raise EvalError("%s: not executable" % (evalfun))
