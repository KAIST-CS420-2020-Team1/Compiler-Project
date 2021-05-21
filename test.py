import ply.lex as lex
import ply.yacc as yacc

# Foo.. idk
def p_foo(p):
    'stmt : stmt + stmt'
    p[0] = p[1] + p[3]

yacc.yacc()

