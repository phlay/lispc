from copy import copy

class LispError(Exception): pass

class LambdaError(LispError): pass



#
# Classes
#
class LispObj:
    def _bake(self, local, binding=False):
        return self

    def _backrefs(self, local, parameter):
        return set()

    def _rewrite(self, stack):
        return self

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


    def _bake(self, local, binding=False):
        if self.is_atom():
            return self

        function = self.head()
        parameter = self.tail()

        # handle special cases first: "quote", "if" and "lambda"
        if type(function) == LispSym:
            if function == "quote":
                if len(parameter) != 1:
                    raise LambdaError("quote needs exactly one parameter")
                return self
            elif function == "if":
                if len(parameter) != 3:
                    raise LambdaError("if needs exactly three parameter")

                return LispList( [ x._bake(local) for x in self ] )

            elif function == "lambda":
                if binding:
                    return LispLambda(self, local)
                else:
                    return LispClosure(self, local)

        # bake function call
        baked_function = function._bake(local, binding=True)
        baked_parameter = [ p._bake(local) for p in parameter ]
        if not baked_function.is_executable():
            raise LambdaError("%s: not executable" % (baked_function))

        if type(baked_function) == LispLambda:
            if baked_function.argc != len(baked_parameter):
                raise LambdaError("%s: expects %d parameter, got %d" %
                        (function,
                         baked_function.argc,
                         len(baked_parameter)))

        return LispList( [baked_function] + baked_parameter )

    def _backrefs(self, local, parameter):
        result = set()
        for sub in self:
            result |= sub._backrefs(local, parameter)

        return result

    def _rewrite(self, stack):
        return LispList( [ x._rewrite(stack) for x in self ] )


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

    def _resolve_local(self, local):
        for i,name in enumerate(reversed(local)):
            if self == name:
                return LispRef(i+1)

        return None

    def _bake(self, local, binding=False):
        local_ref = self._resolve_local(local)
        if local_ref is not None:
            return local_ref

        return self

    def _backrefs(self, local, parameter):
        if self not in parameter:
            ref = self._resolve_local(local)
            if ref is not None:
                return set([(self, ref)])

        return set()


    def is_executable(self):
        return True



class LispRef(int, LispObj):
    def __repr__(self):
        return str(self)

    def __str__(self):
        return '$%d' % (int(self))


    def _rewrite(self, stack):
        return stack[-self]


    def is_executable(self):
        return True



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
    def __init__(self, f, argc=None):
        self.name = f.__name__
        self.function = f
        self.argc = argc
        self.extern = "__" + f.__name__

    def __repr__(self):
        return '<' + self.name + '>'

    def __str__(self):
        return '<' + self.name + '>'

    def is_executable(self):
        return True



class LispLambda(LispObj):

    def __init__(self, expr=None, local=None):
        if expr is not None:
            self._load(expr, local)

    def __str__(self):
        return "( λ %d %s )" % (self.argc, self.body)

    def __repr__(self):
        return str(self)


    def _load(self, expr, local):
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

        self.argc = len(lambda_parameter)
        self.body = lambda_body._bake(local + lambda_parameter)


    def _rewrite(self, stack):
        # build new stack
        newstack = [ LispRef(x+self.argc) if type(x) == LispRef else x
                     for x in stack ]
        newstack += [ LispRef(i) for i in reversed(range(1,self.argc+1)) ]

        # build lambda with rewritten body
        new = LispLambda()
        new.argc = self.argc
        new.body = self.body._rewrite(newstack)
        return new


    def is_executable(self):
        return True




class LispClosure(LispLambda):

    def __init__(self, expr=None, local=None):
        if expr is not None:
            self._load(expr, local)

    def __str__(self):
        values = self.capture_values if self.capture_values else self.capture_indices
        return "( ξ %s %d %s )" % (LispList(values), self.argc, self.body)


    def _load(self, expr, local):
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

        backrefs = lambda_body._backrefs(local, set(lambda_parameter))

        local = lambda_parameter + [ R[0] for R in backrefs ]
        self.capture_indices = [ R[1] for R in backrefs ]
        self.capture_values = None

        self.argc = len(lambda_parameter)
        self.body = lambda_body._bake(local)


    def _rewrite(self, stack):
        # claculate the new captured indices array by skipping all indices that
        # are now resolved
        new_indices = [ i for i in self.capture_indices
                        if type(stack[-i]) == LispRef ]

        # Now run backwards through capture_indices and build a substitution:
        # If an index resolves to a value now put this into substitution,
        # otherwise calculate the position in new_indices this index corresponds
        # to and put this in.
        lost_indices = 0
        substitution = []
        for i in reversed(range(len(self.capture_indices))):
            resolved = stack[-self.capture_indices[i]]
            if type(resolved) == LispRef:
                substitution.insert(0, LispRef(len(self.capture_indices) - i - lost_indices))
            else:
                substitution.insert(0, resolved)
                lost_indices += 1

        # calculate new references to closure's parameters
        for i in range(self.argc):
            substitution.insert(0, LispRef(i + 1 + len(new_indices)))

        # create new closure with rewritten body
        new = LispClosure()
        new.capture_indices = new_indices
        new.capture_values = None
        new.argc = self.argc
        new.body = self.body._rewrite(substitution)
        return new




    def is_executable(self):
        return not bool(self.capture_indices) or bool(self.capture_values)

    def capture(self, stack):
        new = copy(self)
        new.capture_values = [ stack[-i] for i in self.capture_indices ]
        return new

    def resolve(self):
        if self.capture_indices and self.capture_values is None:
            raise LambdaError("resolve closure without captured stack")

        new = LispLambda()
        new.argc = self.argc

        if self.capture_values:
            subst = [ LispRef(i) for i in reversed(range(1, self.argc+1)) ]
            subst += self.capture_values
            new.body = self.body._rewrite(subst)

        else:
            # no rewriting needed
            new.body = self.body

        return new
