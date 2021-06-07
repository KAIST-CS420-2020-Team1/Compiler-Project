import ply.yacc as yacc

precedence = (
    ('right', 'ELSE'),
)

class TranslationUnit:
    def __init__(self, decl):
        self.decls = [decl]
    def add(self, decl):
        self.decls = self.decls + [decl]
        return self
    def decls(self):
        return self.decls

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
        pass

def p_function_definition(t):
    '''function_definition : type_specifier declarator compound_statement'''
    t[2].set_base_type(t[1])
    t[0] = FunctionDefn(t[2], t[3]) # Need to change this

def Declaration():
    def __init__(self, base_type, declarator):
        self.base_type = base_type
        self.declarator = declarator
        pass

def p_declaration_01(t):
    '''declaration : type_specifier declarator SEMICOLON'''
    t[0] = Declaration(t[1], t[2])

def p_type_specifier(t):
    '''type_specifier : INT
                      | FLOAT'''
    t[0] = BaseType(t[1])

def p_declarator_01(t):
    '''declarator : direct_declarator'''
    t[0] = t[1]

def p_declarator_02(t):
    '''declarator : ASTERISK declarator'''
    t[2].set_base_type(PointerType())
    t[0] = t[2]

def p_direct_declarator_01(t):
    '''direct_declarator : ID'''
    t[0] = Declaration(t[1])

def p_direct_declarator_02(t):
    '''direct_declarator : direct_declarator LPAREN parameter_type_list RPAREN'''
    t[1].add_type(FunctionType(t[3]))
    t[0] = t[1]

def p_direct_declarator_03(t):
    '''direct_declarator : direct_declarator LPAREN RPAREN'''
    t[1].add_type(FunctionType(ParamList()))
    t[0] = t[1]

def p_parameter_type_list_01(t):
    '''parameter_type_list : parameter_list'''
    t[0] = t[1]

def p_parameter_type_list_02(t):
    '''parameter_type_list : parameter_list COMMA ELLIPSIS'''
    t[1].has_ellipsis = 1
    t[0] = t[1]

def p_parameter_list_01(t):
    '''parameter_list : parameter_declaration'''
    t[0] = ParamList(t[1])

def p_parameter_list_02(t):
    '''parameter_list : parameter_list COMMA parameter_declaration'''
    t[1].add(t[3])
    t[0] = t[1]

def p_parameter_declaration(t):
    '''parameter_declaration : type_specifier declarator'''
    # NOTE: this is the same code as p_declaration_01!
    p_declaration_01(t)

def p_compound_statement_01(t):
    '''compound_statement : LBRACE declaration_list_opt statement_list RBRACE'''
    t[0] = CompoundStatement(t[2], t[3])

def p_compound_statement_02(t):
    '''compound_statement : LBRACE declaration_list_opt RBRACE'''
    t[0] = CompoundStatement(t[2], NullNode())

def p_expression_statement(t):
    '''expression_statement : expression SEMICOLON'''
    t[0] = t[1]

def p_expression_01(t):
    '''expression : equality_expression'''
    t[0] = t[1]

def p_expression_02(t):    
    '''expression : equality_expression ASSIGN expression
                  | equality_expression EQ_PLUS expression
                  | equality_expression EQ_MINUS expression'''
    t[0] = Binop(t[1], t[3], t[2])

def p_equality_expression_01(t):
    '''equality_expression : relational_expression'''
    t[0] = t[1]

def p_equality_expression_02(t):    
    '''equality_expression : equality_expression EQ relational_expression
                           | equality_expression NOT_EQ relational_expression'''
    t[0] = _get_calculated(Binop(t[1], t[3], t[2]))

def p_relational_expression_01(t):
    '''relational_expression : additive_expression'''
    t[0] = t[1]

def p_relational_expression_02(t):
    '''relational_expression : relational_expression LESS additive_expression
                             | relational_expression GREATER additive_expression
                             | relational_expression LESS_EQ additive_expression
                             | relational_expression GREATER_EQ additive_expression'''
    t[0] = _get_calculated(Binop(t[1], t[3], t[2]))

def p_postfix_expression_01(t):
    '''postfix_expression : primary_expression'''
    t[0] = t[1]

def p_postfix_expression_02(t):
    '''postfix_expression : postfix_expression LPAREN argument_expression_list RPAREN'''
    t[0] = FunctionExpression(t[1], t[3])
    pass

def p_postfix_expression_03(t):
    '''postfix_expression : postfix_expression LPAREN RPAREN'''
    t[0] = FunctionExpression(t[1], ArgumentList())

def p_postfix_expression_04(t):
    '''postfix_expression : postfix_expression LBRACKET expression RBRACKET'''
    t[0] = ArrayExpression(t[1], t[3])

def p_argument_expression_list_01(t):
    '''argument_expression_list : expression'''
    t[0] = ArgumentList(t[1])

def p_argument_expression_list_02(t):
    '''argument_expression_list : argument_expression_list COMMA expression'''
    t[1].add(t[3])
    t[0] = t[1]

def p_unary_expression_01(t):
    '''unary_expression : postfix_expression'''
    t[0] = t[1]

def p_unary_expression_02(t):
    '''unary_expression : MINUS unary_expression'''
    t[0] = _get_calculated(Negative(t[2]))

def p_unary_expression_03(t):
    '''unary_expression : PLUS unary_expression'''
    t[0] = t[2]

def p_unary_expression_03(t):
    '''unary_expression : EXCLAMATION unary_expression'''
    # horrible hack for the '!' operator... Just insert an
    # (expr == 0) into the AST.
    t[0] = _get_calculated(Binop(t[2], Const(0, BaseType('int')), '=='))

def p_unary_expression_04(t):
    '''unary_expression : ASTERISK unary_expression'''
    t[0] = Pointer(t[2])

def p_unary_expression_05(t):
    '''unary_expression : AMPERSAND unary_expression'''
    t[0] = AddrOf(t[2])

def p_mult_expression_01(t):
    '''mult_expression : unary_expression'''
    t[0] = t[1]

def p_mult_expression_02(t):
    '''mult_expression : mult_expression ASTERISK unary_expression
                       | mult_expression DIV unary_expression    
                       | mult_expression MODULO unary_expression'''
    t[0] = _get_calculated(Binop(t[1], t[3], t[2]))

def p_additive_expression_01(t):
    '''additive_expression : mult_expression'''
    t[0] = t[1]

def p_additive_expression_02(t):
    '''additive_expression : additive_expression PLUS mult_expression
                           | additive_expression MINUS mult_expression'''
    t[0] = _get_calculated(Binop(t[1], t[3], t[2]))

def p_primary_expression_01(t):
    '''primary_expression : ID'''
    t[0] = Id(t[1], t.lineno(1))

def p_primary_expression_02(t):
    '''primary_expression : INUMBER'''
    t[0] = Const(int(t[1]), BaseType('int'))

def p_primary_expression_03(t):
    '''primary_expression : FNUMBER'''
    t[0] = Const(float(t[1]), BaseType('double'))

def p_primary_expression_04(t):
    '''primary_expression : CHARACTER'''
    t[0] = Const(ord(eval(t[1])), BaseType('char'))

def p_primary_expression_05(t):
    '''primary_expression : string_literal'''
    t[0] = t[1]

def p_primary_expression_06(t):
    '''primary_expression : LPAREN expression RPAREN'''
    t[0] = t[2]

def p_string_literal_01(t):
    '''string_literal : STRING'''
    t[0] = StringLiteral(eval(t[1]))

def p_string_literal_02(t):
    '''string_literal : string_literal STRING'''
    t[1].append_str(eval(t[2]))
    t[0] = t[1]

def p_statement(t):
    '''statement : compound_statement
                 | expression_statement
                 | selection_statement
                 | iteration_statement
                 | jump_statement'''
    t[0] = t[1]

def p_jump_statement_01(t):
    '''jump_statement : RETURN SEMICOLON'''
    t[0] = ReturnStatement(NullNode())
    
def p_jump_statement_02(t):
    '''jump_statement : RETURN expression SEMICOLON'''
    t[0] = ReturnStatement(t[2])

def p_jump_statement_03(t):
    '''jump_statement : BREAK SEMICOLON'''
    t[0] = BreakStatement()

def p_jump_statement_04(t):
    '''jump_statement : CONTINUE SEMICOLON'''
    t[0] = ContinueStatement()

def p_iteration_statement_01(t):
    '''iteration_statement : WHILE LPAREN expression RPAREN statement'''
    t[0] = WhileLoop(t[3], t[5])

def p_iteration_statement_02(t):
    '''iteration_statement : FOR LPAREN expression_statement expression_statement expression RPAREN statement'''
    t[0] = ForLoop(t[3], t[4], t[5], t[7])

def p_selection_statement_01(t):
    '''selection_statement : IF LPAREN expression RPAREN statement'''
    t[0] = IfStatement(t[3], t[5], NullNode())

def p_selection_statement_02(t):
    '''selection_statement : IF LPAREN expression RPAREN statement ELSE statement'''
    t[0] = IfStatement(t[3], t[5], t[7])

def p_statement_list_02(t):
    '''statement_list : statement'''
    t[0] = StatementList(t[1])

def p_statement_list_03(t):
    '''statement_list : statement_list statement'''
    t[1].add(t[2])
    t[0] = t[1]

def p_empty(t):
    'empty :'
    pass

def p_error(t):
    print ("You've got a syntax error somewhere in your code.")
    print ("It could be around line %d.".format(t.lineno))
    raise ParseError()

yacc.yacc(debug=1)