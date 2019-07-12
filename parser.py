import ply.lex as lex
import ply.yacc as yacc

from lisp import *

class ParseError(LispError): pass


#
# lexer
#
tokens = (
        'LPAR',
        'RPAR',
        'QUOTE',
        'TRUE',
        'NIL',
        'SYM',
        'INT',
        'STR',
        )

t_LPAR = r'\('
t_RPAR = r'\)'
t_QUOTE = r"'"

t_ignore = ' \t'
t_ignore_COMMENT = r';.*'


def t_SYM(t):
    r'[a-zA-Z\+\-\*\/_]\w*'
    t.value = LispSym(t.value)
    return t

def t_TRUE(t):
    r'\#(T|t)'
    t.value = LispTrue()
    return t

def t_NIL(t):
    r'\#[Nn][Ii][Ll]'
    t.value = LispList([])
    return t

def t_INT(t):
    r'-?\d+'
    t.value = LispInt(t.value)
    return t

def t_STR(t):
    r'"[^"]*"'
    t.value = LispStr(t.value[1:-1])
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    raise ParseError('illegal character: %s' % (t.value[0]))


lexer = lex.lex()


#
# yacc
#

def p_item_sym(p):
    'item : SYM'
    p[0] = p[1]

def p_item_true(p):
    'item : TRUE'
    p[0] = p[1]

def p_item_int(p):
    'item : INT'
    p[0] = p[1]

def p_item_str(p):
    'item : STR'
    p[0] = p[1]

def p_item_list(p):
    'item : list'
    p[0] = p[1]

def p_quoted_item(p):
    'item : QUOTE item'
    p[0] = LispList([ LispSym('quote'), p[2] ])

def p_sequence_s(p):
    'sequence : item'
    p[0] = [ p[1] ]

def p_sequence(p):
    'sequence : sequence item'
    p[0] = p[1] + [ p[2] ]

def p_list_empty(p):
    'list : LPAR RPAR'
    p[0] = LispList([])

def p_list_nil(p):
    'list : NIL'
    p[0] = p[1]

def p_list(p):
    'list : LPAR sequence RPAR'
    p[0] = LispList(p[2])

def p_error(p):
    if p:
        raise ParseError('illegal syntax: %s' % (p))
    else:
        raise ParseError('illegal end of data')


line_parser = yacc.yacc(optimize=False, debug=False, start = 'item')
file_parser = yacc.yacc(optimize=False, debug=False, start = 'sequence')

def load_file(fn):
    with open(fn, 'r') as f:
        return file_parser.parse(f.read())

