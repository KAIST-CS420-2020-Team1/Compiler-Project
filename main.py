import sys

import functools
import itertools
import parse
import CFG
import structure
import stack
import analysis

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

class MainContext:
    def __init__(self, ast):
        # TODO CFG?

        # Structures
        self.global_table = analysis.get_symbol_table(ast.decls)
        self.func_tables = structure.Function_Table()
        for fndecl in filter(analysis.is_instance(parse.FunctionDefn), ast.decls):
            blocks = analysis.desugar_body(fndecl.body)
            print("{}:\n{}".format(fndecl.declarator, blocks))
            entry = analysis.get_function_entry(fndecl)
            self.func_tables.insert(entry[0], entry[1], entry[2], entry[3], entry[4], stack.ValueTable([]))

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
    parsed = parser.parse(input_file.read(), tracking=True)
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

