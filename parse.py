import ply.yacc as yacc
import scanner
import sys

tokens = scanner.tokens

precedence = (
    ('right', 'ELSE'),
)

class TranslationUnit:
    def __init__(self, decl):
        self.decls = decl
    def add(self, decl):
        self.decls = self.decls + [decl]
        return self

class ParseError(Exception):
    "Exception raised whenever a parsing error occurs."

def p_translation_unit_01(t):
    '''translation_unit : external_declaration'''
    t[0] = TranslationUnit(t[1])

def p_translation_unit_02(t):
    '''translation_unit : translation_unit external_declaration'''
    t[0] = t[1].add(t[2])

def p_external_declaration(t):
    '''external_declaration : function_definition
                            | declaration'''
    t[0] = t[1]


class FunctionDefn():
    def __init__(self, r_type, declarator, body):
        self.r_type = r_type
        self.declarator = declarator
        self.body = body

class Declaration():
    def __init__(self, base_type, declarator):
        self.base_type = base_type
        self.declarator = declarator
        self.is_const = False
        self.value_expr = ''

def p_function_definition(t):
    '''function_definition : type_specifier declarator body'''
    t[2].set_base_type(t[1])
    t[0] = FunctionDefn(t[2], t[3]) # Need to change this


def p_declaration_01(t):
    '''declaration : type_specifier declarator SEMICOLON'''
    t[0] = Declaration(t[1], t[2])
def p_declaration_02(t): # TODO Is this legal
    '''declaration : CONST declaration'''
    t[0] = t[2]
    t[0].is_const = True
def p_declaration_03(t):
    '''declaration : type_specifier declarator ASSIGN expression SEMICOLON'''
    t[0] = Declaration(t[1], t[2])
    t[0].value_expr = t[4]


def p_decl_list_01(t):
    '''declaration_list : '''
    t[0] = []
def p_decl_list_02(t):
    '''declaration_list : declaration_list declaration'''
    t[0] = t[1] + [ t[2] ]


class Float():
    def __init__(self):
        self.type = "float"
    pass
class Int():
    def __init__(self):
        self.type = "int"


class Identifier():
    def __init__(self, name):
        self.name = name

class Asterisked():
    def __init__(self, base):
        self.base = base
class Arrayed():
    def __init__(self, base, len):
        self.base = base
        self.len = len
class Fn_Declarator():
    def __init__(self, base, params):
        self.base = base
        self.params = params

def p_type_specifier_01(t):
    '''type_specifier : INT'''
    t[0] = Float()
def p_type_specifier_02(t):
    '''type_specifier : FLOAT'''
    t[0] = Float()
def p_type_specifier_03(t):
    '''type_specifier : VOID'''
    t[0] = []


def p_declarator_01(t):
    '''declarator : direct_declarator'''
    t[0] = t[1]
def p_declarator_02(t):
    '''declarator : ASTERISK declarator'''
    t[0] = Asterisked(t[2])


def p_direct_declarator_01(t):
    '''direct_declarator : ID'''
    t[0] = Identifier(t[1])
def p_direct_declarator_02(t):
    '''direct_declarator : direct_declarator LEFT_PARENTHESIS parameter_list RIGHT_PARENTHESIS'''
    t[0] = Fn_Declarator(t[1], t[3])
def p_direct_declarator_03(t):
    '''direct_declarator : direct_declarator LEFT_BRACKET INT_NUM RIGHT_BRACKET'''
    t[0] = Arrayed(t[1], t[3])


def p_parameter_list_01(t):
    '''parameter_list : parameter_declaration'''
    t[0] = [ t[1] ]
def p_parameter_list_02(t):
    '''parameter_list : parameter_list COMMA parameter_declaration'''
    t[0] = t[1] + [ t[3] ]
def p_parameter_list_03(t):
    '''parameter_list : '''
    t[0] = []

def p_parameter_declaration(t):
    '''parameter_declaration : type_specifier declarator'''
    p_declaration_01(t) # Same designation


class Body:
    def __init__(self, decls, stmts):
        self.decls = decls
        self.stmts = stmts

def p_body(t):
    '''body : LEFT_BRACE declaration_list statement_list RIGHT_BRACE'''
    t[0] = Body(t[2], t[3])

class Const:
    def __init__(self, value, type):
        self.value = value
        self.type = type # Int or Float
class UniOp:
    def __init__(self, operand, op):
        self.op = op
        self.operand = operand
class BinOp:
    def __init__(self, left, right, op):
        self.op = op
        self.left = left
        self.right = right
class FuncCall:
    def __init__(self, fn_name, args):
        self.fn_name = fn_name
        self.args = args
class ArrayIdx:
    def __init__(self, name, index):
        self.name = name
        self.index = index

def p_expression_statement(t):
    '''expression_statement : expression SEMICOLON'''
    t[0] = t[1]

def p_expression_01(t):
    '''expression : equality_expression'''
    t[0] = t[1]
def p_expression_02(t):    
    '''expression : equality_expression ASSIGN expression
                  | equality_expression ASSIGN_PLUS expression
                  | equality_expression ASSIGN_MINUS expression'''
    t[0] = BinOp(t[1], t[3], t[2])

def p_equality_expression_01(t):
    '''equality_expression : relational_expression'''
    t[0] = t[1]

def p_equality_expression_02(t):    
    '''equality_expression : equality_expression EQUAL relational_expression
                           | equality_expression NOT_EQUAL relational_expression'''
    t[0] = BinOp(t[1], t[3], t[2])
def p_relational_expression_01(t):
    '''relational_expression : additive_expression'''
    t[0] = t[1]
def p_relational_expression_02(t):
    '''relational_expression : relational_expression LESS additive_expression
                             | relational_expression GREATER additive_expression
                             | relational_expression LESS_EQUAL additive_expression
                             | relational_expression GREATER_EQUAL additive_expression'''
    t[0] = BinOp(t[1], t[3], t[2])

def p_postfix_expression_01(t):
    '''postfix_expression : primary_expression'''
    t[0] = t[1]
def p_postfix_expression_02(t):
    '''postfix_expression : postfix_expression LEFT_PARENTHESIS argument_expression_list RIGHT_PARENTHESIS'''
    t[0] = FuncCall(t[1], t[3])
def p_postfix_expression_03(t):
    '''postfix_expression : postfix_expression LEFT_BRACKET expression RIGHT_BRACKET'''
    t[0] = ArrayIdx(t[1], t[3])

def p_argument_expression_list_01(t):
    '''argument_expression_list : expression'''
    t[0] = [ t[1] ]
def p_argument_expression_list_02(t):
    '''argument_expression_list : argument_expression_list COMMA expression'''
    t[0] = t[1] + [ t[3] ]
def p_argument_expression_list_03(t):
    '''argument_expression_list : '''
    t[0] = []


def p_unary_expression_01(t):
    '''unary_expression : postfix_expression'''
    t[0] = t[1]
def p_unary_expression_02(t):
    '''unary_expression : MINUS unary_expression'''
    t[0] = UniOp(t[2], '-')
def p_unary_expression_03(t):
    '''unary_expression : PLUS unary_expression'''
    t[0] = t[2]
def p_unary_expression_04(t):
    '''unary_expression : ASTERISK unary_expression'''
    t[0] = UniOp(t[2], '*')
def p_unary_expression_05(t):
    '''unary_expression : AMPERSAND unary_expression'''
    t[0] = UniOp(t[2], '&')

def p_mult_expression_01(t):
    '''mult_expression : unary_expression'''
    t[0] = t[1]
def p_mult_expression_02(t):
    '''mult_expression : mult_expression ASTERISK unary_expression
                       | mult_expression DIV unary_expression    
                       | mult_expression MOD unary_expression'''
    t[0] = BinOp(t[1], t[3], t[2])

def p_additive_expression_01(t):
    '''additive_expression : mult_expression'''
    t[0] = t[1]
def p_additive_expression_02(t):
    '''additive_expression : additive_expression PLUS mult_expression
                           | additive_expression MINUS mult_expression'''
    t[0] = BinOp(t[1], t[3], t[2])

def p_primary_expression_01(t):
    '''primary_expression : ID'''
    t[0] = Identifier(t[1])
def p_primary_expression_02(t):
    '''primary_expression : INT_NUM'''
    t[0] = Const(int(t[1]), Int())
def p_primary_expression_03(t):
    '''primary_expression : FLOAT_NUM'''
    t[0] = Const(float(t[1]), Float())
def p_primary_expression_04(t):
    '''primary_expression : LEFT_PARENTHESIS expression RIGHT_PARENTHESIS'''
    t[0] = t[2]


# While or For loop
class Iteration:
    # loopDesc: condition for while loop, ForDesc for for loop
    def __init__(self, loopDesc, body):
        self.loopDesc = loopDesc
        self.body = body
class ForDesc:
    def __init__(self, init, iter, until):
        self.init = init
        self.iter = iter
        self.until = until
        pass

# If Statement
class Selection:
    def __init__(self, cond, thenB, elseB):
        self.cond = cond
        self.thenB = thenB
        self.elseB = elseB
        self.hasElse = elseB != []

def p_statement(t):
    '''statement : body
                 | expression_statement
                 | selection_statement
                 | iteration_statement'''
    t[0] = t[1]

def p_iteration_statement_01(t):
    '''iteration_statement : WHILE LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement'''
    t[0] = Iteration(t[3], t[5])
def p_iteration_statement_02(t):
    '''iteration_statement : FOR LEFT_PARENTHESIS expression_statement expression_statement expression RIGHT_PARENTHESIS statement'''
    t[0] = Iteration(ForDesc(t[3], t[4], t[5]), t[7])

def p_selection_statement_01(t):
    '''selection_statement : IF LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement'''
    t[0] = Selection(t[3], t[5], [])
def p_selection_statement_02(t):
    '''selection_statement : IF LEFT_PARENTHESIS expression RIGHT_PARENTHESIS statement ELSE statement'''
    t[0] = Selection(t[3], t[5], t[7])

def p_statement_list_01(t):
    '''statement_list : '''
    t[0] = []
def p_statement_list_02(t):
    '''statement_list : statement_list statement'''
    t[0] = t[1] + [ t[2] ]

def p_error(t):
    print ("Syntax Error, content: {}".format(t))
    raise ParseError()

parser = yacc.yacc(debug=1)

def test_parse():
    input_file = open(sys.argv[1])
    lines = input_file.readlines()
    input_file.close()

    strings = ""
    for line in lines:
        strings += (line + "\n")

    parser.parse(strings)
    print('Done')

if __name__ == '__main__':
    test_parse()
