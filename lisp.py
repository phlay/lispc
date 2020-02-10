from copy import copy

class LispError(Exception): pass

class LambdaError(LispError): pass


class LispObj:

    def is_true(self):
        return True

    def is_atom(self):
        return True

    def is_head(self, name):
        return False

    def is_executable(self):
        return False

    def head(self):
        raise LispError("head only defined for list")

    def tail(self):
        raise LispError("tail only defined for list")



class LispList(list, LispObj):
    def __str__(self):
        # special case for quote
        if len(self) == 2 and type(self[0]) == LispSym and self[0] == 'quote':
            return "'%s" % (str(self[1]))
        # special case for NIL
        if len(self) == 0:
            return "#NIL"

        return '(' + ' '.join(map(repr, self)) + ')'

    def __repr__(self):
        return str(self)

    def head(self):
        if len(self) == 0:
            raise LispError("head of empty list is not defined")

        return self[0]

    def tail(self):
        if len(self) == 0:
            raise LispError("tail of empty list is not defined")

        return LispList(self[1:])

    def is_true(self):
        return len(self) > 0

    def is_atom(self):
        return len(self) == 0

    def is_executable(self):
        if len(self) == 0:
            return True

        head = self.head()
        if type(head) == LispSym:
            return True

        return head.is_executable()


    def is_head(self, name):
        if len(self) > 0 and type(self[0]) == LispSym and self[0] == name:
            return True

        return False


class LispSym(str, LispObj):
    def __repr__(self):
        return str(self)

    def is_executable(self):
        return True


class LispRef(int, LispObj):
    def __repr__(self):
        return str(self)

    def is_executable(self):
        return True

    def __str__(self):
        return '$%d' % (int(self))


class LispInt(int, LispObj):
    def is_executable(self):
        return False


class LispReal(float, LispObj):
    def is_executable(self):
        return False


class LispStr(str, LispObj):
    def __repr__(self):
        return '"' + str(self) + '"'

    def is_executable(self):
        return False

    def is_true(self):
        return len(self) > 0

class LispTrue(LispObj):
    def __str__(self):
        return '#T'

    def __repr__(self):
        return str(self)


class LispBuiltin(LispObj):
    def __init__(self, f, argc = None, side = False):
        self.name = f.__name__
        self.function = f
        self.argc = argc
        self.side_effect = side
        self.extern = "__" + f.__name__

    def __repr__(self):
        return '<' + self.name + '>'

    def __str__(self):
        return '<' + self.name + '>'

    def is_executable(self):
        return True





class LispLambda(LispObj):

    def __init__(self, expr, local = None, closure = False):
        if local is None:
            local = []

        if not expr.is_head("lambda"):
            raise LambdaError("%s: not a lambda" % (expr))

        if len(expr) != 3:
            raise LambdaError("lambda needs two parameter")

        lambda_parameter = expr[1]
        lambda_body = expr[2]

        if len(lambda_parameter) != len(set(lambda_parameter)):
            raise LambdaError("%s: parameter symbols are not unique"
                    % (lambda_parameter))

        if closure:
            backrefs = LispLambda.find_backrefs(lambda_body, set(lambda_parameter), local)
            local = lambda_parameter + [ R[0] for R in backrefs ]
            self.capture_indices = [ R[1] for R in backrefs ]
            self.capture_values = None

        else:
            local = local + lambda_parameter

        self.closure = closure and self.capture_indices
        self.argc = len(lambda_parameter)
        self.body = self.process(lambda_body, local)


    def __str__(self):
        if self.closure:
            values = self.capture_values if self.capture_values else self.capture_indices
            return "( ξ %d %s %s )" % \
                    (self.argc, LispList(values), self.body)
        else:
            return "( λ %d %s )" % (self.argc, self.body)

    def __repr__(self):
        return str(self)

    def is_executable(self):
        return True

    def is_closure(self):
        return self.closure

    def capture(self, stack):
        if self.closure:
            new = copy(self)
            new.capture_values = [ stack[-i] for i in self.capture_indices ]
            return new

        return self

    def process(self, expr, local, exe=False):
        if expr.is_atom():
            if type(expr) == LispSym:
                local_ref = LispLambda.resolve_local_sym(expr, local)
                if local_ref is not None:
                    return local_ref

            return expr

        function = expr.head()
        parameter = expr.tail()

        if type(function) == LispSym:
            if function == "quote":
                if len(parameter) != 1:
                    raise LambdaError("quote needs exactly one parameter")
                return expr
            elif function == "if":
                if len(parameter) != 3:
                    raise EvalError("if needs exactly three parameter")

                condition = self.process(parameter[0], local)
                case_true = self.process(parameter[1], local)
                case_false = self.process(parameter[2], local)

                return LispList([ LispSym("if"),
                                  condition,
                                  case_true,
                                  case_false ])

            elif function == "lambda":
                return LispLambda(expr, local, closure=(not exe))


        # process function call
        processed_function = self.process(function, local, exe=True)
        processed_parameter = LispList([ self.process(p, local) for p in parameter ])
        if not processed_function.is_executable():
            raise LambdaError("%s: not executable" % (processed_function))

        return LispList( [processed_function] + processed_parameter )


    #
    # class methods
    #
    def resolve_local_sym(sym, local):
        for i,name in enumerate(reversed(local)):
            if sym == name:
                return LispRef(i+1)

        return None

    def find_backrefs(expr, parameter, local):
        result = set()
        if expr.is_atom():
            if type(expr) == LispSym and expr not in parameter:
                local_ref = LispLambda.resolve_local_sym(expr, local)
                if local_ref is not None:
                    result = set([(expr, local_ref)])
        else:
            for sub in expr:
                result = result.union( LispLambda.find_backrefs(sub, parameter, local) )

        return result
