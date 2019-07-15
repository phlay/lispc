class LispError(Exception): pass


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
