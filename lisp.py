import copy

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
        if type(head) == LispSym and head == "λ":
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
    def __init__(self, expr, local = None):
        if local is None:
            local = []

        if not expr.is_head("lambda"):
            raise LambdaError("%s: not a lambda" % (expr))

        lambda_parameter = expr[1]
        lambda_body = expr[2]

        if len(lambda_parameter) != len(set(lambda_parameter)):
            raise LambdaError("%s: parameter symbols are not unique"
                    % (lambda_parameter))

        self.max_ref = 0
        self.stack = LispList([])
        self.local = local + [""] + lambda_parameter
        self.argc = len(lambda_parameter)
        self.body = self.bake(lambda_body)

    def __str__(self):
        return "( λ %d %s )" % (self.argc, self.body)

    def __repr__(self):
        return str(self)


    def closure(self, stack):
        n = self.max_ref - self.argc - 1
        if n > 0:
            result = copy.copy(self)
            result.stack = stack[-n:].copy()
        else:
            result = self

        return result


    def resolve_local_sym(self, sym):
        for i,name in enumerate(reversed(self.local)):
            if sym == name:
                n = i + 1

                if n > self.max_ref:
                    self.max_ref = n

                return LispRef(n)

        return None

    def bake(self, expr):
        if expr.is_atom():
            if type(expr) == LispSym:
                local_ref = self.resolve_local_sym(expr)
                if local_ref is not None:
                    return local_ref

                return expr

            if type(expr) == LispRef:
                if int(expr) <= len(local):
                    return expr
                return self.stack[len(local)-int(expr)]

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

                condition = self.bake(parameter[0])
                case_true = self.bake(parameter[1])
                case_false = self.bake(parameter[2])

                return LispList([ LispSym("if"),
                                  condition,
                                  case_true,
                                  case_false ])

            elif function == "lambda":
                return LispLambda(expr, self.local)

        if type(function) == LispLambda:
            raise LambdaError("internal error - baking LispLambda")


        # compile function call
        compiled_expr = LispList([ self.bake(p) for p in expr ])
        compiled_function = compiled_expr.head()

        if not compiled_function.is_executable():
            raise LambdaError("function is not executable: %s" % (compiled_function))

        return compiled_expr
