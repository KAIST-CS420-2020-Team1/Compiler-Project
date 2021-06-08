import ply.yacc as yacc
import scanner
import sys

tokens = scanner.tokens

precedence = (
    ('right', 'ELSE'),
)

# Register to subs to update
class Lined:
    def __init__(self, subs):
        self.subs = subs
    # Sets line, and returns the last line
    def set_line(self, line):
        self.line_num = line
        for sub in self.subs:
            line = sub.set_line(line)
        return line
class SingleLined(Lined):
    def __init__(self):
        super().__init__([])
    def set_line(self, line):
        self.line_num = line
        return line + 1

# Translation Unit, holds global declarations or function declarations
class TranslationUnit(Lined):
    def __init__(self, decls):
        super().__init__(decls)
        self.decls = decls
        self.set_line(0)
    def __str__(self):
        return "\n".join([decl.__str__() for decl in self.decls])

class ParseError(Exception):
    "Exception raised whenever a parsing error occurs."

def p_translation_unit(t):
    '''translation_unit : top_level_list'''
    t[0] = TranslationUnit(t[1])

def p_top_level_list_01(t):
    '''top_level_list : top_level_declaration'''
    t[0] = [ t[1] ]
def p_top_level_list_02(t):
    '''top_level_list : top_level_list top_level_declaration'''
    t[0] = t[1] + [ t[2] ]

def p_external_declaration(t):
    '''top_level_declaration : function_definition
                            | declaration'''
    t[0] = t[1]

# Desugars base type and declarator
def desugar_declarator(base_type, ator):
    if(isinstance(ator, Asterisked)):
        tp, at = desugar_declarator(base_type, ator.base)
        return Asterisked(tp), at
    elif(isinstance(ator, Arrayed)):
        tp, at = desugar_declarator(base_type, ator.base)
        return Arrayed(tp, ator.len), at
    else:
        return base_type, ator

# Need to look into declarator for * and []
class FunctionDefn(Lined):
    def __init__(self, r_type, declarator, body):
        super().__init__([])
        self.r_type = r_type
        self.declarator = declarator
        self.body = body
    def desugar_type_decl(self):
        return desugar_declarator(self.r_type, self.declarator)
    def set_line(self, line):
        self.line_num = line
        line = self.body.set_line(line + 1)
        return line
    def __str__(self):
        return "[ret: {}, decl: {} >> \n{}]".format(self.r_type, self.declarator, self.body)

class EachDecl():
    def __init__(self, type, name):
        self.type = type
        self.name = name
        self.value = None
    def __str__(self):
        return "{} : {} = {}".format(self.name, self.type, self.value)

    def From(base_type, ator):
        if isinstance(ator, Assigned):
            decl = EachDecl.From(base_type, ator.decl_in)
            decl.value = ator.value
            return decl
        elif(isinstance(ator, Asterisked)):
            decl = EachDecl.From(base_type, ator.base)
            decl.type = Asterisked(decl.type)
            return decl
        elif(isinstance(ator, Arrayed)):
            decl = EachDecl.From(base_type, ator.base)
            decl.type = Arrayed(decl.type, ator.len)
            return decl
        elif(isinstance(ator, Identifier)):
            return EachDecl(base_type, ator.name)
        else:
            raise ValueError("Illegal value")

# Need to look into declarator for * and []
class Declaration(SingleLined):
    def __init__(self, base_type, decl_assigns):
        self.base_type = base_type
        self.decl_assigns = decl_assigns
        self.is_const = False
        # print("\n".join(map(str, self.desugar())))
    def desugar(self):
        return [EachDecl.From(self.base_type, da) for da in self.decl_assigns]
    def __str__(self):
        return "{}> [base: {}, declare: [{}], const: {}]".format(self.line_num, self.base_type, ",".join(map(str, self.decl_assigns)), self.is_const)
class Assigned():
    def __init__(self, declarator, value):
        self.decl_in = declarator
        self.value = value
    def __str__(self):
        return "{} := {}".format(self.decl_in, self.value)

def p_function_definition(t):
    '''function_definition : type_specifier declarator body'''
    t[0] = FunctionDefn(t[1], t[2], t[3])


def p_declaration_01(t):
    '''declaration : type_specifier declarator_assign_list SEMICOLON'''
    t[0] = Declaration(t[1], t[2])
def p_declaration_02(t):
    '''declaration : CONST declaration'''
    t[0] = t[2]
    t[0].is_const = True

def p_declarator_assign_01(t):
    '''declarator_assign : declarator'''
    t[0] = t[1]
def p_declarator_assign_02(t):
    '''declarator_assign : declarator ASSIGN expression'''
    t[0] = Assigned(t[1], t[3])

def p_decl_assign_list_01(t):
    '''declarator_assign_list : declarator_assign'''
    t[0] = [ t[1] ]
def p_decl_assign_list_02(t):
    '''declarator_assign_list : declarator_assign_list COMMA declarator_assign'''
    t[0] = t[1] + [ t[3] ]


def p_decl_list_01(t):
    '''declaration_list : '''
    t[0] = []
def p_decl_list_02(t):
    '''declaration_list : declaration_list declaration'''
    t[0] = t[1] + [ t[2] ]


class Float():
    def __init__(self):
        self.type = "float"
    def __str__(self):
        return "float"
class Int():
    def __init__(self):
        self.type = "int"
    def __str__(self):
        return "int"

class Identifier():
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name

class Asterisked():
    def __init__(self, base):
        self.base = base
    def __str__(self):
        return "<ptr>{}".format(self.base)
class Arrayed():
    def __init__(self, base, len):
        self.base = base
        self.len = len
    def __str__(self):
        return "{}[{}]".format(self.base, self.len)
class Fn_Declarator():
    def __init__(self, base, params):
        self.base = base
        self.params = params
    def __str__(self):
        return "{} w params {}".format(self.base, self.params)

def p_type_specifier_01(t):
    '''type_specifier : INT'''
    t[0] = Int()
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
    '''declarator : MUL declarator'''
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
    t[0] = Declaration(t[1], [ t[2] ])


class Body(Lined):
    def __init__(self, decls, stmts):
        super().__init__(decls + stmts)
        self.decls = decls
        self.stmts = stmts
    def __str__(self):
        return "\n".join(map(str, self.subs))

def p_body(t):
    '''body : LEFT_BRACE declaration_list statement_list RIGHT_BRACE'''
    t[0] = Body(t[2], t[3])

class Const:
    def __init__(self, value, type):
        self.value = value
        self.type = type # Int or Float
    def __str__(self):
        return "{}{}".format(self.value, self.type)
class UniOp:
    def __init__(self, operand, op):
        self.op = op
        self.operand = operand
        self.postfix = False
    def __str__(self):
        if(self.postfix):
            return "({}){}".format(self.operand, self.op)
        else:
            return "{}({})".format(self.op, self.operand)
class BinOp:
    def __init__(self, left, right, op):
        self.op = op
        self.left = left
        self.right = right
    def __str__(self):
        return "{} {} {}".format(self.left, self.op, self.right)
class FuncCall:
    def __init__(self, fn_name, args):
        self.fn_name = fn_name
        self.args = args
    def __str__(self):
        return "{}({})".format(self.fn_name, ",".join(map(str, self.args)))
class ArrayIdx:
    def __init__(self, name, index):
        self.name = name
        self.index = index
    def __str__(self):
        return "{}.[{}]".format(self.name, self.index)

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
def p_postfix_expression_04(t):
    '''postfix_expression : postfix_expression PLUS_PLUS'''
    t[0] = UniOp(t[1], '++')
    t[0].postfix = True
def p_postfix_expression_05(t):
    '''postfix_expression : postfix_expression MINUS_MINUS'''
    t[0] = UniOp(t[1], '--')
    t[0].postfix = True

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
    '''unary_expression : MUL unary_expression'''
    t[0] = UniOp(t[2], '*')
def p_unary_expression_05(t):
    '''unary_expression : AMPERSAND unary_expression'''
    t[0] = UniOp(t[2], '&')
def p_unary_expression_06(t):
    '''unary_expression : PLUS_PLUS unary_expression'''
    t[0] = UniOp(t[2], '++')
def p_unary_expression_07(t):
    '''unary_expression : MINUS_MINUS unary_expression'''
    t[0] = UniOp(t[2], '--')

def p_mult_expression_01(t):
    '''mult_expression : unary_expression'''
    t[0] = t[1]
def p_mult_expression_02(t):
    '''mult_expression : mult_expression MUL unary_expression
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


class Statement(SingleLined):
    def __init__(self, content):
        self.content = content
        self.returning = False
    def __str__(self):
        return "{}> {} {}".format(self.line_num, ["", "return"][self.returning], self.content)

# While or For loop
class Iteration(Lined):
    # loopDesc: condition for while loop, ForDesc for for loop
    def __init__(self, loopDesc, body):
        super().__init__([])
        self.loopDesc = loopDesc
        self.body = body
    def set_line(self, line):
        self.line_num = line
        line = self.body.set_line(line + 1)
        return line
    def __str__(self):
        return "ite[{}] [\n{}\n]".format(self.loopDesc, self.body)
class ForDesc:
    def __init__(self, init, iter, until):
        self.init = init
        self.iter = iter
        self.until = until
    def __str__(self):
        return "{} | {} | {}".format(self.init, self.iter, self.until)

# If Statement
class Selection(Lined):
    def __init__(self, cond, thenB, elseB):
        super().__init__([thenB, elseB])
        self.cond = cond
        self.thenB = thenB
        self.elseB = elseB
        self.hasElse = elseB != []
    def set_line(self, line):
        self.line_num = line
        line = self.thenB.set_line(line + 1) # TODO Same-line statement - "need significant \n"
        if self.hasElse:
            line = self.elseB.set_line(line)
        return line
    def __str__(self):
        return "cond[{}] [\n{}\n] [{}]".format(self.cond, self.thenB, self.elseB)

def p_statement(t):
    '''statement : body
                 | return_statement
                 | expression_statement
                 | selection_statement
                 | iteration_statement'''
    if not isinstance(t[1], Lined):
        t[0] = Statement(t[1])
    else:
        t[0] = t[1]

def p_return_statement(t):
    '''return_statement : RETURN expression SEMICOLON'''
    t[0] = Statement(t[2])
    t[0].returning = True


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
    result = parser.parse(input_file.read())
    print('Done')
    print('')
    print(result)

if __name__ == '__main__':
    test_parse()
