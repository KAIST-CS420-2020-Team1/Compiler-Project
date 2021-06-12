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
        self.CFG = CFG.generate_graph(ast)
        self.CFG_pc = self.CFG[0]
        self.done = 0

        self.global_table = analysis.get_symbol_table(ast.decls)
        self.func_tables = CFG.function_table
        self.val_stack = CFG.value_stack
        self.call_stack = CFG.call_stack

    def begin(self):
        self.cur_func_table = self.func_tables.table["main"]
        pass

    def cmd_next(self, num=1):
        # TODO Runs #num statements
        cfg_node = self.CFG_pc.next_line()
        iter = 1

        while ((cfg_node != None) and (iter < num)):
            cfg_node = cfg_node.next_line()
            iter += 1

        if (cfg_node == None):
            print("End of program")
            self.done = 1

        self.CFG_pc = cfg_node

        return

    def cmd_print(self, var_name):
        vtable = self.func_tables.table[self.call_stack.top().name].ref_value

        if vtable.has_value(var_name):
            print(val_str(vtable.get_value(var_name)))
            return

        '''vtable = self.global_table.ref.ref_value

        if vtable.has_value(var_name):
            print(val_str(vtable.get_value(var_name)))
            return'''

        print("Invisible variable")
        return

    def cmd_trace(self, var_name):
        vtable = self.func_tables.table[self.call_stack.top().name].ref_value

        if vtable.has_value(var_name):
            print(history_str(var_name, vtable.get_history(var_name)))
            return

        '''vtable = self.global_table.ref
        if vtable.has_value(var_name):
            print(history_str(var_name, vtable.get_history(var_name)))
            return'''

        print("Invisible variable")
        return


if __name__ == '__main__':
    parser = parse.parser

    input_file = open(sys.argv[1])
    parsed = parser.parse(input_file.read(), tracking=True)
    parsed = analysis.desugar_ast(parsed)
    input_file.close()
    print(parsed)
    ctxt = MainContext(parsed)

    ctxt.begin()

    while True:
        line = input('>> ')
        if line == '':
            break

        args = line.split(' ')
        if args[0] == 'next':
            if (ctxt.done == 0):
                if len(args) == 1:
                    ctxt.cmd_next()
                elif args[1].isnumeric():
                    ctxt.cmd_next(int(args[1]))  # Placeholder
                else:
                    print("Incorrect command usage: try 'next[lines]")
            else:
                print("End of program")
        elif args[0] == 'print' and len(args) == 2:
            ctxt.cmd_print(args[1])
        elif args[0] == 'trace' and len(args) == 2:
            ctxt.cmd_trace(args[1])
        else:
            print("Invalid typing of the variable name")