import itertools

import parse
import structure
import stack

# Syntax Analysis with Desugaring

def is_instance(cl):
    return lambda x: isinstance(x, cl)


# Body as list of blocks
class BlockBody:
    def __init__(self, blocks):
        self.blocks = blocks
    def __str__(self):
        return "\n".join(["[{}]".format(",".join([str(line) for line in block])) for block in self.blocks])


def is_branching(stmt):
    return isinstance(stmt, parse.Iteration) or isinstance(stmt, parse.Selection)

# Desugars the function body
def desugar_body(body):
    # TODO How to take care of function calls in dividing basic blocks
    # Likely no need to exclude function call itself from basic block
    lines = body.decls + body.stmts
    lines = desugar_lines(lines)
    grouped = list(map(lambda x: list(x[1]), itertools.groupby(lines, key=is_branching)))
    return BlockBody(grouped)

# Desugar mixed statements
def desugar_line(line):
    if(isinstance(line, parse.Declaration)):
        return line.desugar()
    elif(isinstance(line, parse.Selection)):
        line.thenB = desugar_body(line.thenB)
        if line.hasElse:
            line.elseB = desugar_body(line.elseB)
        return [line]
    elif(isinstance(line, parse.Iteration)):
        line.body = desugar_body(line.body)
        return [line]
    elif(isinstance(line, parse.Statement)): # For checking 
        check_stmt(line.content)
        return [line]
    else:
        return [line]

# Desugar declration into EachDecl inside mixed statements
# Can also be used to handle toplevel
def desugar_lines(lines):
    return list(itertools.chain(*map(desugar_line, lines)))

def check_lvalue(expr):
    if(isinstance(expr, parse.UniOp)):
        if(expr.op != '*'):
            print("operator of {} is not lvalue".format(expr))
            raise ValueError("semantic error")
        else:
            check_lvalue(expr.operand)
    elif(isinstance(expr, parse.BinOp)):
        print("operator of {} is not lvalue".format(expr))
        raise ValueError("semantic error")
    elif(isinstance(expr, parse.ArrayIdx)):
        check_lvalue(expr.array)
    elif(isinstance(expr, parse.FuncCall)):
        print("function call {} is not lvalue".format(expr))
        raise ValueError("semantic error")
    elif(isinstance(expr, parse.Const)):
        print("constant {} is not lvalue".format(expr))
        raise ValueError("semantic error")

def check_stmt(expr):
    if(isinstance(expr, parse.UniOp)):
        if(expr.op in ['++', '--']): # Changes
            check_lvalue(expr.operand)
        elif(expr.op == '*' and isinstance(expr.operand, parse.Const)):
            print("illegal constant dereferencing".format(expr))
            raise ValueError("semantic error")
        check_stmt(expr.operand)
    elif(isinstance(expr, parse.BinOp)):
        if(expr.op in ['+=', '-=', '=']): # Assignment
            check_lvalue(expr.left)
        check_stmt(expr.left)
        check_stmt(expr.right)
    elif(isinstance(expr, parse.ArrayIdx)):
        check_stmt(expr.array)
        check_stmt(expr.index)
    elif(isinstance(expr, parse.FuncCall)):
        for arg in expr.args:
            check_stmt(arg)


# EachDecl into Symbol Entry
def as_symbol_entry(each):
    if isinstance(each.type, parse.Arrayed):
        if isinstance(each.type.base, parse.Arrayed):
            raise ValueError("double array is not supported, {}", each.type)
        return (each.name, each.type.base, each.type.len)
    else:
        return (each.name, each.type, 1)

# Symbol table from Declaration
def get_symbol_table(decls):
    vars = filter(is_instance(parse.EachDecl), decls)
    vars = map(as_symbol_entry, vars)
    var_names = map(lambda x: x[0], vars)
    sym_table = structure.Symbol_Table(stack.ValueTable(var_names))
    for var in vars:
        sym_table.insert(var[0], var[1], var[2])
    return sym_table

# Get function entry from FunctionDefn
def get_function_entry(fndecl):
    r_type, decl = fndecl.desugar_type_decl()
    if(not isinstance(decl, parse.Fn_Declarator)):
        raise ValueError("{} is not a function", fndecl)
    if(not isinstance(decl.base, parse.Identifier)):
        raise ValueError("{} has complex type signature", fndecl)
    symbol_table = get_symbol_table(fndecl.body.decls)
    params = desugar_lines(decl.params) # Reuse to turn it into EachDecl
    p_types = map(lambda x: x.type, params)
    return (decl.base.name, r_type, p_types, fndecl.line_num, symbol_table)
