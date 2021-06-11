import ply.lex as lex
import ply.yacc as yacc
import scanner
import sys

tokens = scanner.tokens

precedence = (
    ('right', 'ELSE'),
)

# Register to subs to update
class Lined:
    # Sets line, and returns the last line
    def set_line(self, line):
        self.line_num = line
        return line

# Translation Unit, holds global declarations or function declarations
class TranslationUnit:
    def __init__(self, decls):
        self.decls = decls
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
        self.r_type = r_type
        self.declarator = declarator
        self.body = body
    def desugar_type_decl(self):
        return desugar_declarator(self.r_type, self.declarator)
    def __str__(self):
        return "{}> [ret: {}, decl: {} >> \n{}]".format(self.line_num, self.r_type, self.declarator, self.body)

class EachDecl(Lined):
    def __init__(self, type, name, line):
        self.type = type
        self.name = name
        self.value = None
        self.line_num = line
    def __str__(self):
        return "{} : {} = {}".format(self.name, self.type, self.value)

    def From(line, base_type, ator):
        if isinstance(ator, Assigned):
            decl = EachDecl.From(line, base_type, ator.decl_in)
            decl.value = ator.value
            return decl
        elif(isinstance(ator, Asterisked)):
            decl = EachDecl.From(line, base_type, ator.base)
            decl.type = Asterisked(decl.type)
            return decl
        elif(isinstance(ator, Arrayed)):
            decl = EachDecl.From(line, base_type, ator.base)
            decl.type = Arrayed(decl.type, ator.len)
            return decl
        elif(isinstance(ator, Identifier)):
            return EachDecl(base_type, ator.name, line)
        else:
            raise ValueError("Illegal value")

# Need to look into declarator for * and []
class Declaration(Lined):
    def __init__(self, base_type, decl_assigns):
        self.base_type = base_type
        self.decl_assigns = decl_assigns
        self.is_const = False
    def desugar(self):
        return [EachDecl.From(self.line_num, self.base_type, da) for da in self.decl_assigns]
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
    t[0].set_line(t.lineno(1))


def p_declaration_01(t):
    '''declaration : type_specifier declarator_assign_list SEMICOLON'''
    t[0] = Declaration(t[1], t[2])
    t[0].set_line(t.lineno(1))
def p_declaration_02(t):
    '''declaration : CONST declaration'''
    t[0] = t[2]
    t[0].is_const = True

def p_declarator_assign_01(t):
    '''declarator_assign : declarator'''
    t[0] = t[1]
def p_declarator_assign_02(t):
    '''declarator_assign : declarator ASSIGN expr'''
    t[0] = Assigned(t[1], t[3])

def p_decl_assign_list_01(t):
    '''declarator_assign_list : declarator_assign'''
    t[0] = [ t[1] ]
def p_decl_assign_list_02(t):
    '''declarator_assign_list : declarator_assign_list COMMA declarator_assign'''
    t[0] = t[1] + [ t[3] ]


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
class Void():
    def __init__(self):
        self.type = "void"
    def __str__(self):
        return "void"

class Identifier():
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return str(self.name)

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
        return "{} w {}".format(self.base, self.params)

def p_type_specifier_01(t):
    '''type_specifier : INT'''
    t[0] = Int()
def p_type_specifier_02(t):
    '''type_specifier : FLOAT'''
    t[0] = Float()
def p_type_specifier_03(t):
    '''type_specifier : VOID'''
    t[0] = Void()

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
def p_parameter_list_04(t):
    '''parameter_list : VOID'''
    t[0] = []

def p_parameter_declaration(t):
    '''parameter_declaration : type_specifier declarator'''
    t[0] = Declaration(t[1], [ t[2] ])
    t[0].set_line(t.lineno(1))


class Body(Lined):
    def __init__(self, stmts):
        self.stmts = stmts
    def __str__(self):
        return "\n".join(map(str, self.stmts))

def p_decl_stmt(t):
    '''decl_stmt : declaration
                 | statement'''
    t[0] = t[1]
def p_decl_stmt_list_01(t):
    '''decl_stmt_list : '''
    t[0] = []
def p_decl_stmt_list_02(t):
    '''decl_stmt_list : decl_stmt_list decl_stmt'''
    t[0] = t[1] + [ t[2] ]

def p_body(t):
    '''body : LEFT_BRACE decl_stmt_list RIGHT_BRACE'''
    t[0] = Body(t[2])

class Const:
    def __init__(self, value, type):
        self.value = value
        self.type = type # Int or Float
    def __str__(self):
        return "{}{}".format(self.value, self.type)
# ++, --, &, *, +, -
class UniOp:
    def __init__(self, operand, op):
        self.op = op
        self.operand = operand
        self.postfix = False
    def __str__(self):
        if(self.postfix):
            return "({}{})".format(self.operand, self.op)
        else:
            return "({}{})".format(self.op, self.operand)
# +, -, *, /, %
# >, >=, <, <=, ==, !=
class BinOp:
    def __init__(self, left, right, op):
        self.op = op
        self.left = left
        self.right = right
    def __str__(self):
        return "( {} {} {} )".format(self.left, self.op, self.right)

# =, +=, -=
class Assign:
    def __init__(self, lvalue, rvalue, op):
        self.op = op
        self.lvalue = lvalue
        self.rvalue = rvalue
    def __str__(self):
        return "( {} {} {} )".format(self.lvalue, self.op, self.rvalue)

class FuncCall:
    def __init__(self, fn_name, args):
        self.fn_name = fn_name
        self.args = args
    def __str__(self):
        return "{}({})".format(self.fn_name, ",".join(map(str, self.args)))
class ArrayIdx:
    def __init__(self, array, index):
        self.array = array
        self.index = index
    def __str__(self):
        return "{}[{}]".format(self.array, self.index)

def p_expr_statement(t):
    '''expr_statement : expr SEMICOLON'''
    t[0] = t[1]

def p_expr_01(t):
    '''expr : equal_expr'''
    t[0] = t[1]
def p_expr_02(t):
    '''expr : equal_expr ASSIGN expr
                  | equal_expr ASSIGN_PLUS expr
                  | equal_expr ASSIGN_MINUS expr'''
    t[0] = Assign(t[1], t[3], t[2])
    t[0].line_num = t.lineno(1)

def p_equal_expr_01(t):
    '''equal_expr : compare_expr'''
    t[0] = t[1]

def p_equal_expr_02(t):
    '''equal_expr : equal_expr EQUAL compare_expr
                           | equal_expr NOT_EQUAL compare_expr'''
    t[0] = BinOp(t[1], t[3], t[2])
def p_compare_expr_01(t):
    '''compare_expr : add_expr'''
    t[0] = t[1]
def p_compare_expr_02(t):
    '''compare_expr : compare_expr LESS add_expr
                             | compare_expr GREATER add_expr
                             | compare_expr LESS_EQUAL add_expr
                             | compare_expr GREATER_EQUAL add_expr'''
    t[0] = BinOp(t[1], t[3], t[2])

def p_postfix_expr_01(t):
    '''postfix_expr : prim_expr'''
    t[0] = t[1]
def p_postfix_expr_02(t):
    '''postfix_expr : postfix_expr LEFT_PARENTHESIS arg_expr_list RIGHT_PARENTHESIS'''
    t[0] = FuncCall(t[1], t[3])
def p_postfix_expr_03(t):
    '''postfix_expr : postfix_expr LEFT_BRACKET expr RIGHT_BRACKET'''
    t[0] = ArrayIdx(t[1], t[3])
def p_postfix_expr_04(t):
    '''postfix_expr : postfix_expr PLUS_PLUS'''
    t[0] = UniOp(t[1], '++')
    t[0].postfix = True
def p_postfix_expr_05(t):
    '''postfix_expr : postfix_expr MINUS_MINUS'''
    t[0] = UniOp(t[1], '--')
    t[0].postfix = True

def p_arg_expr_list_01(t):
    '''arg_expr_list : expr'''
    t[0] = [ t[1] ]
def p_arg_expr_list_02(t):
    '''arg_expr_list : arg_expr_list COMMA expr'''
    t[0] = t[1] + [ t[3] ]
def p_arg_expr_list_03(t):
    '''arg_expr_list : '''
    t[0] = []


def p_unary_expr_01(t):
    '''unary_expr : postfix_expr'''
    t[0] = t[1]
def p_unary_expr_02(t):
    '''unary_expr : MINUS unary_expr'''
    t[0] = UniOp(t[2], '-')
def p_unary_expr_03(t):
    '''unary_expr : PLUS unary_expr'''
    t[0] = t[2]
def p_unary_expr_04(t):
    '''unary_expr : MUL unary_expr'''
    t[0] = UniOp(t[2], '*')
def p_unary_expr_05(t):
    '''unary_expr : AMPERSAND unary_expr'''
    t[0] = UniOp(t[2], '&')
def p_unary_expr_06(t):
    '''unary_expr : PLUS_PLUS unary_expr'''
    t[0] = UniOp(t[2], '++')
def p_unary_expr_07(t):
    '''unary_expr : MINUS_MINUS unary_expr'''
    t[0] = UniOp(t[2], '--')

def p_mult_expr_01(t):
    '''mult_expr : unary_expr'''
    t[0] = t[1]
def p_mult_expr_02(t):
    '''mult_expr : mult_expr MUL unary_expr
                       | mult_expr DIV unary_expr
                       | mult_expr MOD unary_expr'''
    t[0] = BinOp(t[1], t[3], t[2])

def p_add_expr_01(t):
    '''add_expr : mult_expr'''
    t[0] = t[1]
def p_add_expr_02(t):
    '''add_expr : add_expr PLUS mult_expr
                           | add_expr MINUS mult_expr'''
    t[0] = BinOp(t[1], t[3], t[2])

def p_prim_expr_01(t):
    '''prim_expr : ID'''
    t[0] = Identifier(t[1])
def p_prim_expr_02(t):
    '''prim_expr : INT_NUM'''
    t[0] = Const(int(t[1]), Int())
def p_prim_expr_03(t):
    '''prim_expr : FLOAT_NUM'''
    t[0] = Const(float(t[1]), Float())
def p_prim_expr_04(t):
    '''prim_expr : LEFT_PARENTHESIS expr RIGHT_PARENTHESIS'''
    t[0] = t[2]


class Statement(Lined):
    def __init__(self, content):
        self.content = content
        self.returning = False
    def __str__(self):
        return "{}> {} {}".format(self.line_num, ["", "return"][self.returning], self.content)

# While or For loop. Its body is Body
class Iteration(Lined):
    # loopDesc: condition expression for while loop, ForDesc for for loop
    def __init__(self, loopDesc, body):
        if not isinstance(body, Body):
            body = Body([ body ]) # Single-lined body
        self.loopDesc = loopDesc
        self.body = body
    def __str__(self):
        return "{}> ite[{}] [\n{}\n]".format(self.line_num, self.loopDesc, self.body)
class ForDesc:
    def __init__(self, init, until, iter):
        self.init = init
        self.until = until
        self.iter = iter
    def __str__(self):
        return "{} | {} | {}".format(self.init, self.until, self.iter)

# If Statement. Its body is Body
class Selection(Lined):
    def __init__(self, cond, thenB, elseB):
        if not isinstance(thenB, Body):
            thenB = Body([ thenB ]) # Single-lined body
        if elseB != [] and not isinstance(elseB, Body):
            elseB = Body([ elseB ]) # Single-lined body
        self.cond = cond
        self.thenB = thenB
        self.elseB = elseB
        self.hasElse = elseB != []
    def __str__(self):
        return "{}> cond[{}] [\n{}\n] [{}]".format(self.line_num, self.cond, self.thenB, self.elseB)

class PrintStmt(Lined):
    def __init__(self, format, value):
        self.format = format
        self.value = value # Value to print
        pass
    def __str__(self):
        return "{}> printf({}, {})".format(self.line_num, self.format, self.value)

def p_statement(t):
    '''statement : body
                 | print_statement
                 | return_statement
                 | expr_statement
                 | selection_statement
                 | iteration_statement'''
    if not isinstance(t[1], Lined): # expr_statement
        t[0] = Statement(t[1])
    else:
        t[0] = t[1]
    t[0].set_line(t.lineno(1))

def p_print_statement_01(t):
    '''print_statement : PRINTF LEFT_PARENTHESIS STRING COMMA expr RIGHT_PARENTHESIS SEMICOLON'''
    t[0] = PrintStmt(t[3], t[5])
    t[0].set_line(t.lineno(1))
def p_print_statement_02(t):
    '''print_statement : PRINTF LEFT_PARENTHESIS STRING RIGHT_PARENTHESIS SEMICOLON'''
    t[0] = PrintStmt(t[3], None)
    t[0].set_line(t.lineno(1))


def p_return_statement(t):
    '''return_statement : RETURN expr SEMICOLON'''
    t[0] = Statement(t[2])
    t[0].returning = True


def p_iteration_statement_01(t):
    '''iteration_statement : WHILE LEFT_PARENTHESIS expr RIGHT_PARENTHESIS statement'''
    t[0] = Iteration(t[3], t[5])
def p_iteration_statement_02(t):
    '''iteration_statement : FOR LEFT_PARENTHESIS expr_statement expr_statement expr RIGHT_PARENTHESIS statement'''
    t[0] = Iteration(ForDesc(t[3], t[4], t[5]), t[7])

def p_selection_statement_01(t):
    '''selection_statement : IF LEFT_PARENTHESIS expr RIGHT_PARENTHESIS statement'''
    t[0] = Selection(t[3], t[5], [])

def p_selection_statement_02(t):
    '''selection_statement : IF LEFT_PARENTHESIS expr RIGHT_PARENTHESIS statement ELSE statement'''
    t[0] = Selection(t[3], t[5], t[7])


def p_error(t):
    if isinstance(t, Lined):
        print ("Syntax Error, line: {}, content: {}".format(t.line_num, t))
    elif isinstance(t, lex.LexToken):
        print ("Syntax Error, line: {}, content: {}".format(t.lineno, t))
    else:
        print ("Syntx Error, content: {}".format(t)) # Not able to perform..
    raise ParseError()

parser = yacc.yacc(debug=1)

def test_parse():
    input_file = open(sys.argv[1])
    result = parser.parse(input_file.read(), tracking=True)
    print('Done')
    print('')
    print(result)
    return result

if __name__ == '__main__':
    test_parse()