import sys

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
    "\n".join([
        "{} = {} at line {}".format(var_name, val_str(val), line)
        for (val, line) in history])

class MainContext:
    def __init__(self, ast):
        globals = []
        for decl in ast.decls:
            if isinstance(decl, parse.Declaration):
                # TODO Insert declarations
                desugared = decl.desugar()
                pass
            elif isinstance(decl, parse.FunctionDefn):
                # TODO Insert functions
                pass
            else:
                raise ValueError("Illegal Parse")

        # Structures
        self.global_table = structure.Symbol_Table(stack.ValueTable([])) # TODO Globals
        self.func_tables = structure.Function_Table()

        # Stacks
        self.val_stack = stack.ValueStack()
        self.call_stack = stack.CallStack()

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
            print(history_str(vtable.get_history(var_name)))
            return
        vtable = self.global_table.ref
        if vtable.has_value(var_name):
            print(history_str(vtable.get_history(var_name)))
            return
        print("{} not found".format(var_name))


if __name__ == '__main__':
    parser = parse.parser

    input_file = open(sys.argv[1])
    parsed = parser.parse(input_file.read())
    input_file.close()
    ctxt = MainContext(parsed)

    while True:
        line = input('>>')
        if line == '':
            break
        if line.startswith('next'):

            pass
        if line.startswith('print'):
            pass
        if line.startswith('trace'):
            pass

