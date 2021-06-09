import itertools

import parse
import structure
import stack

# TODO L-value
# TODO Block -> AST

def is_instance(cl):
    return lambda x: isinstance(x, cl)

def as_symbol_entry(each):
    if isinstance(each.type, parse.Arrayed):
        if isinstance(each.type.base, parse.Arrayed):
            raise ValueError("double array is not supported, {}", each.type)
        return (each.name, each.type.base, each.type.len)
    else:
        return (each.name, each.type, 1)

def desugar_var_decls(decls):
    vars = filter(is_instance(parse.Declaration), decls)
    vars = list(itertools.chain(*map(parse.Declaration.desugar, vars)))
    return vars

def get_symbol_table(decls):
    vars = desugar_var_decls(decls)
    vars = map(as_symbol_entry, vars)
    var_names = map(lambda x: x[0], vars)
    sym_table = structure.Symbol_Table(stack.ValueTable(var_names))
    for var in vars:
        sym_table.insert(var[0], var[1], var[2])
    return sym_table

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