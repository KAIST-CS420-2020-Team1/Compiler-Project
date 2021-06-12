import itertools
import functools

import parse
import structure
import stack

# Syntax Analysis with Desugaring
# Note desugar_ast

def is_instance(cl):
    return lambda x: isinstance(x, cl)

class TempInfo:
    def __init__(self):
        self.available_id = 0
    def next(self):
        id = self.available_id
        self.available_id = id + 1
        return id

temp_info = TempInfo()

class Temp_Ident():
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "[|{}|]".format(self.name)

# Representa a function call along with putting it into some ref
# Replaces FuncCall
class Fn_Call_Stmt(parse.Lined):
    def __init__(self, fn_name, args, store_name):
        self.fn_name = fn_name
        self.args = args
        self.store_name = store_name
    def __str__(self):
        return "{}> {} = {}({})".format(self.line_num, self.store_name, self.fn_name, ",".join(map(str, self.args)))

def is_branching(stmt):
    as_stmt = isinstance(stmt, parse.Iteration) or isinstance(stmt, parse.Selection)
    as_fn_call = isinstance(stmt, Fn_Call_Stmt) or (isinstance(stmt, parse.Statement) and stmt.returning)
    return as_stmt or as_fn_call

# Desugars the entire AST (for the source code file)
def desugar_ast(ast: parse.TranslationUnit):
    top_decls = list(filter(is_instance(parse.Declaration), ast.decls))
    fns = list(filter(is_instance(parse.FunctionDefn), ast.decls))
    desugar_tdecls = desugar_lines(top_decls)
    for decl in desugar_tdecls:
        if decl.value != None and not isinstance(decl.value, parse.Const):
            print('Nonconstant value {} not allowed in top level declarations', decl.value)
            raise ValueError('semantic error')
    for fn in fns:
        fn.body = desugar_body(fn.body)
    return parse.TranslationUnit(desugar_lines(top_decls) + fns)

# Desugars the function body
def desugar_body(body: parse.Body):
    lines = body.stmts
    lines = desugar_lines(lines)
    #grouped = list(map(lambda x: list(x[1]), itertools.groupby(lines, key=is_branching)))
    #return BlockBody(grouped)
    return parse.Body(lines)

# Desugar mixed statements
def desugar_line(stmt):
    if(isinstance(stmt, parse.Declaration)):
        return stmt
        # return [ sub for decl in stmt.desugar() for sub in desugar_decl(decl) ]
    elif(isinstance(stmt, parse.Selection)):
        exes, stmt.cond = desugar_expr(stmt.line_num, stmt.cond)
        for exe in exes:
            exe.set_line(stmt.line_num)
        stmt.thenB = desugar_body(stmt.thenB)
        if stmt.hasElse:
            stmt.elseB = desugar_body(stmt.elseB)
        return exes + [ stmt ]
    elif(isinstance(stmt, parse.Iteration)):
        desc = stmt.loopDesc
        if(isinstance(desc, parse.ForDesc)):
            exes, res = desugar_expr(stmt.line_num, desc.init)
            exe2, res2 = desugar_expr(stmt.line_num, desc.until)
            exe3, res3 = desugar_expr(stmt.line_num, desc.iter)
            if exe2 != [] or exe3 != []:
                print("line {}: function call in condition/iteration not yet supported, in {}".format(stmt.line_num, stmt))
                raise ValueError("semantic error")
            desc.init = res
        else:
            # While only has conditional statement
            exes = []
            exe2, res2 = desugar_expr(stmt.line_num, desc)
            if exe2 != []:
                print("line {}: function call in condition/iteration not yet supported, in {}".format(stmt.line_num, stmt))
                raise ValueError("semantic error")
        for exe in exes:
            exe.set_line(stmt.line_num)
        stmt.body = desugar_body(stmt.body)
        return exes + [stmt]
    elif(isinstance(stmt, parse.Statement)):
        exes, res = desugar_expr(stmt.line_num, stmt.content)
        stmt.content = res
        for exe in exes:
            exe.set_line(stmt.line_num)
        return exes + [stmt]
    elif(isinstance(stmt, parse.PrintStmt)):
        if stmt.value != None:
            exes, res = desugar_expr(stmt.line_num, stmt.value)
            stmt.value = res
            for exe in exes:
                exe.set_line(stmt.line_num)
            return exes + [stmt]
        else:
            return [ stmt ]
    else:
        raise TypeError("Unexpected type", type(stmt))

# Desugar declration into EachDecl inside mixed statements
# Can also be used to handle toplevel
def desugar_lines(lines):
    return list(itertools.chain(*map(desugar_line, lines)))

# Desugar a declaration into mix of expressions and declarations
def desugar_decl(each: parse.EachDecl):
    if each.value != None:
        exes, each.value = desugar_expr(each.line_num, each.value)
        for exe in exes:
            exe.set_line(each.line_num)
        return exes + [ each ]
    else:
        return [ each ]

def is_lvalue(expr):
    if(isinstance(expr, parse.Identifier)):
        return True
    elif(isinstance(expr, parse.UniOp)):
        return expr.op == '*' and is_lvalue(expr.operand)
    elif(isinstance(expr, parse.BinOp)):
        return False
    elif(isinstance(expr, parse.Assign)):
        return False
    elif(isinstance(expr, parse.ArrayIdx)):
        return is_lvalue(expr.array)
    elif(isinstance(expr, parse.FuncCall)):
        return False
    elif(isinstance(expr, parse.Const)):
        return False

def check_stmt(line, expr):
    if(isinstance(expr, parse.UniOp)):
        if(expr.op in ['++', '--']): # Changes
            if(not is_lvalue(expr.operand)):
                print("line {}: {} is not lvalue".format(line, expr.operand))
                raise ValueError("semantic error")
        elif(expr.op == '*' and isinstance(expr.operand, parse.Const)):
            print("line {}: illegal constant dereferencing in {}".format(line, expr))
            raise ValueError("semantic error")
        check_stmt(line, expr.operand)
    elif(isinstance(expr, parse.Assign)):
        if(not is_lvalue(expr.lvalue)):
            print("line {}: {} is not lvalue".format(line, expr.lvalue))
            raise ValueError("semantic error")
        is_lvalue(expr.lvalue)
        check_stmt(line, expr.lvalue)
        check_stmt(line, expr.rvalue)
    elif(isinstance(expr, parse.BinOp)):
        check_stmt(line, expr.left)
        check_stmt(line, expr.right)
    elif(isinstance(expr, parse.ArrayIdx)):
        check_stmt(line, expr.array)
        check_stmt(line, expr.index)
    elif(isinstance(expr, parse.FuncCall)):
        for arg in expr.args:
            check_stmt(line, arg)


# Desugars a single expr into tuple of (expr_to_execute, result_to_use)
def desugar_expr(line, expr):
    check_stmt(line, expr)
    if(isinstance(expr, parse.UniOp)): # Nothing to desugar
        exe, res = desugar_expr(line, expr.operand)
        return (exe, parse.UniOp(res, expr.op))
    elif(isinstance(expr, parse.BinOp)):
        exel, resl = desugar_expr(line, expr.left)
        exer, resr = desugar_expr(line, expr.right)
        return (exel + exer, parse.BinOp(resl, resr, expr.op))
    elif(isinstance(expr, parse.Assign)):
        if expr.op == '=' and isinstance(expr.lvalue, parse.Identifier) and isinstance(expr.rvalue, parse.FuncCall):
            return ([Fn_Call_Stmt(expr.rvalue.fn_name, expr.rvalue.args, expr.lvalue)], expr.lvalue)
        else:
            exel, resl = desugar_expr(line, expr.lvalue)
            exer, resr = desugar_expr(line, expr.rvalue)
            return (exel + exer, parse.Assign(resl, resr, expr.op))
    elif(isinstance(expr, parse.ArrayIdx)):
        exel, resl = desugar_expr(line, expr.array)
        exer, resr = desugar_expr(line, expr.index)
        return (exel + exer, parse.ArrayIdx(resl, resr))
    elif(isinstance(expr, parse.FuncCall)):
        temp_var = Temp_Ident(temp_info.next())
        call = Fn_Call_Stmt(expr.fn_name, expr.args, temp_var)
        return ([call], temp_var)
    elif(isinstance(expr, parse.Identifier)):
        return ([], expr)
    elif(isinstance(expr, parse.Const)):
        return ([], expr)


# NOTE Not used
# EachDecl into Symbol Entry
def as_symbol_entry(each: parse.EachDecl):
    if isinstance(each.type, parse.Arrayed):
        if isinstance(each.type.base, parse.Arrayed):
            raise ValueError("double array is not supported, {}", each.type)
        return (each.name, each.type.base, each.type.len)
    else:
        return (each.name, each.type, 1)

# NOTE Not used
# Symbol table from Declaration
def get_symbol_table(decls: parse.Declaration):
    vars = filter(is_instance(parse.EachDecl), decls)
    vars = map(as_symbol_entry, vars)
    # var_names = map(lambda x: x[0], vars)
    sym_table = structure.Symbol_Table(None) # ref?
    for var in vars:
        sym_table.insert(var[0], var[1], var[2])
    return sym_table

# NOTE Not used
# Get function entry from FunctionDefn
def get_function_entry(fndecl: parse.FunctionDefn):
    r_type, decl = fndecl.desugar_type_decl()
    if(not isinstance(decl, parse.Fn_Declarator)):
        raise ValueError("{} is not a function", fndecl)
    if(not isinstance(decl.base, parse.Identifier)):
        raise ValueError("{} has complex type signature", fndecl)
    symbol_table = get_symbol_table(fndecl.body.stmts)
    params = desugar_lines(decl.params) # Reuse to turn it into EachDecl
    p_types = map(lambda x: x.type, params)
    return (decl.base.name, r_type, p_types, fndecl.line_num, symbol_table)
