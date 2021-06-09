import itertools

import parse
import structure
import stack

# Syntax Analysis

# TODO L-value?

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
    else:
        return [line]

# Desugar declration into EachDecl inside mixed statements
def desugar_lines(lines):
    return list(itertools.chain(*map(desugar_line, lines)))


# EachDecl into Symbol Entry
def as_symbol_entry(each):
    if isinstance(each.type, parse.Arrayed):
        if isinstance(each.type.base, parse.Arrayed):
            raise ValueError("double array is not supported, {}", each.type)
        return (each.name, each.type.base, each.type.len)
    else:
        return (each.name, each.type, 1)

# Desugar lists of declarations
def desugar_var_decls(decls):
    vars = filter(is_instance(parse.Declaration), decls)
    vars = list(itertools.chain(*map(parse.Declaration.desugar, vars)))
    return vars

# Symbol table from Declaration
def get_symbol_table(decls):
    vars = desugar_var_decls(decls)
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
    params = desugar_var_decls(decl.params)
    p_types = map(lambda x: x.name, params)
    return (decl.base.name, r_type, p_types, fndecl.line_num, symbol_table)
