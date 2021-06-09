import sys

import functools
import itertools
import parse
import CFG
import structure
import stack

def val_str(value):
    if value == None:
        return 'N/A'
    else:
        return str(value)
def history_str(var_name, history):
    if history == []:
        return "{} not yet initialized".format(var_name)
    else:
        return "\n".join([
            "{} = {} at line {}".format(var_name, val_str(val), line)
            for (val, line) in history])

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

class MainContext:
    def __init__(self, ast):
        # TODO Same named variable disallowed. Type mismatch(pointer/array nesting level)
        # TODO L-value
        # TODO Block -> AST
        # TODO CFG

        # Structures
        self.global_table = get_symbol_table(ast.decls)
        self.func_tables = structure.Function_Table()
        for fndecl in filter(is_instance(parse.FunctionDefn), ast.decls):
            entry = get_function_entry(fndecl)
            self.func_tables.insert(entry[0], entry[1], entry[2], entry[3], entry[4])

        # Stacks
        self.val_stack = stack.ValueStack()
        self.call_stack = stack.CallStack()

    def begin(self):
        self.cur_func_table = self.func_tables.table["main"]
        pass

    def next(self, num = 1):
        # TODO Runs #num statements
        0

    def print(self, var_name):
        vtable = self.cur_func_table.ref.ref
        if vtable.has_value(var_name):
            print(val_str(vtable.get_value(var_name)))
            return
        vtable = self.global_table.ref
        if vtable.has_value(var_name):
            print(val_str(vtable.get_value(var_name)))
            return
        print("{} not found".format(var_name))

    def trace(self, var_name):
        vtable = self.cur_func_table.ref.ref
        if vtable.has_value(var_name):
            print(history_str(var_name, vtable.get_history(var_name)))
            return
        vtable = self.global_table.ref
        if vtable.has_value(var_name):
            print(history_str(var_name, vtable.get_history(var_name)))
            return
        print("{} not found".format(var_name))


if __name__ == '__main__':
    parser = parse.parser

    input_file = open(sys.argv[1])
    parsed = parser.parse(input_file.read())
    input_file.close()
    ctxt = MainContext(parsed)

    ctxt.begin()

    while True:
        line = input('>> ')
        if line == '':
            break

        args = line.split(' ')
        if args[0] == 'next':
            if len(args) == 1:
                ctxt.next()
            elif args[1].isnumeric():
                ctxt.next(int(args[1])) # Placeholder
        if args[0] == 'print' and len(args) == 2:
            ctxt.print(args[1])
        if args[0] == 'trace' and len(args) == 2:
            ctxt.trace(args[1])

