import sys

import functools
import itertools
import parse
import CFG
import structure
import stack
import analysis

import re


def val_str(value):
    if (value == None):
        return "N/A"
    else:
        if (isinstance(value, list)):
            ret = False
            for elem in value:
                if (elem != None):
                    ret = True
                    break
            if (ret):
                return str(value)
            else:
                return "N/A"
        else:
            return str(value)


def history_str(var, idx, history):
    if history == []:
        return "{} not yet initialized".format(var)
    else:
        if (idx == None):
            return "\n".join([
                "{} = {} at line {}".format(var, val_str(val), line)
                for (val, line) in history])
        else:
            return "\n".join([
                "{} = {} at line {}".format(var, val_str(val[idx]), line)
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
        self.global_value_table = CFG.global_value_table

    def begin(self):
        self.cur_func_table = self.func_tables.table["main"]
        pass

    def referencing(self, addr):
        if (addr == None):
            return None

        if (len(self.call_stack.called) == 0):
            vtable = self.cur_func_table.ref_value
        else:
            vtable = self.func_tables.table[self.call_stack.top().name].ref_value

        return vtable.get_value_from_address(addr)

    def dereferencing(self, name):
        if (name == None):
            return None

        if (len(self.call_stack.called) == 0):
            vtable = self.cur_func_table.ref_value
        else:
            vtable = self.func_tables.table[self.call_stack.top().name].ref_value
        if not vtable.has_value(name):
            vtable = self.global_value_table

        return vtable.get_address(name)

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

    def cmd_print(self, var, idx):
        if (len(self.call_stack.called) == 0):
            vtable = self.cur_func_table.ref_value
        else:
            vtable = self.func_tables.table[self.call_stack.top().name].ref_value

        if vtable.has_value(var):
            if (idx == None):
                print(val_str(vtable.get_value(var)))
            else:
                arr = vtable.get_value(var)
                if ((-len(arr) <= idx) and (idx < len(arr))):
                    print(val_str(vtable.get_value(var)[idx]))
                else:
                    print("Invisible variable")
            return
        elif self.global_value_table.has_value(var):
            if (idx == None):
                print(val_str(self.global_value_table.get_value(var)))
            else:
                arr = self.global_value_table.get_value(var)
                if ((-len(arr) <= idx) and (idx < len(arr))):
                    print(val_str(self.global_value_table.get_value(var)[idx]))
                else:
                    print("Invisible variable")
            return

        '''vtable = self.global_table.ref.ref_value

        if vtable.has_value(var_name):
            print(val_str(vtable.get_value(var_name)))
            return'''

        print("Invisible variable")
        return

    def cmd_trace(self, var, idx):
        if (len(self.call_stack.called) == 0):
            vtable = self.cur_func_table.ref_value
        else:
            vtable = self.func_tables.table[self.call_stack.top().name].ref_value

        if vtable.has_value(var):
            if (idx == None):
                print(history_str(var, idx, vtable.get_history(var)))
            else:
                arr = vtable.get_value(var)
                if ((-len(arr) <= idx) and (idx < len(arr))):
                    print(history_str(var, idx, vtable.get_history(var)))
                else:
                    print("Invisible variable")
            return
        elif self.global_value_table.has_value(var):
            if (idx == None):
                print(history_str(var, idx, self.global_value_table.get_history(var)))
            else:
                arr = self.global_value_table.get_value(var)
                if ((-len(arr) <= idx) and (idx < len(arr))):
                    print(history_str(var, idx, self.global_value_table.get_history(var)))
                else:
                    print("Invisible variable")
            return

        '''vtable = self.global_table.ref
        if vtable.has_value(var_name):
            print(history_str(var_name, vtable.get_history(var_name)))
            return'''

        print("Invisible variable")
        return


def print_recursive_ref_pointer(ctxt, expr):
    if (expr[0] == "*"):
        if (expr[1] == "&"):
            return ctxt.referencing(print_recursive_deref_pointer(ctxt, expr[1:]))
        else:
            return ctxt.referencing(print_recursive_ref_pointer(ctxt, expr[1:]))
    elif (expr[0] == "&"):
        if (expr[1] == "&"):
            return ctxt.referencing(print_recursive_deref_pointer(ctxt, expr[1:]))
        else:
            return ctxt.referencing(print_recursive_ref_pointer(ctxt, expr[1:]))
    else:
        var = re.findall(r"([A-Za-z_][\w]*$)", expr)
        if (len(var) == 0):
            if (expr.isnumeric()):
                return int(expr)
            else:
                return None
        var = var[0]
        if (len(ctxt.call_stack.called) == 0):
            vtable = ctxt.cur_func_table.ref_value
        else:
            vtable = ctxt.func_tables.table[ctxt.call_stack.top().name].ref_value
        return vtable.get_value(var)


def print_recursive_deref_pointer(ctxt, expr):
    if (expr[0] == "*"):
        if (expr[1] == "*"):
            return ctxt.dereferencing(print_recursive_ref_pointer(ctxt, expr[1:]))
        else:
            return ctxt.dereferencing(print_recursive_deref_pointer(ctxt, expr[1:]))
    elif (expr[0] == "&"):
        if (expr[1] == "*"):
            return ctxt.dereferencing(print_recursive_ref_pointer(ctxt, expr[1:]))
        else:
            return ctxt.dereferencing(print_recursive_deref_pointer(ctxt, expr[1:]))
    else:
        var = re.findall(r"([A-Za-z_][\w]*$)", expr)
        var = var[0]
        return var


if __name__ == '__main__':
    parser = parse.parser

    input_file = open(sys.argv[1])
    parsed = parser.parse(input_file.read(), tracking=True)
    parsed = analysis.desugar_ast(parsed)
    input_file.close()
    ctxt = MainContext(parsed)

    ctxt.begin()
    while True:
        line = input('>> ')
        if line == '':
            break

        rule_1 = re.compile(r"([A-Za-z_][\w]*$)")
        rule_2 = re.compile(r"([A-Za-z_][\w]*\[\d+\]$)")

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
            if (rule_1.match(args[1])):
                var = re.findall(r"([A-Za-z_][\w]*$)", args[1])
                var = var[0]
                idx = None
                ctxt.cmd_print(var, idx)
            elif (rule_2.match(args[1])):
                var = re.findall(r"([A-Za-z_][\w]*)", args[1])
                var = var[0]
                idx = re.findall(r"(\[\d+\])", args[1])
                idx = idx[0]
                idx = int(idx[1:-1])
                ctxt.cmd_print(var, idx)
            elif (args[1][0] == "*"):
                print(val_str(print_recursive_ref_pointer(ctxt, args[1])))
            elif (args[1][0] == "&"):
                print(val_str(print_recursive_deref_pointer(ctxt, args[1])))
            else:
                print("Invalid typing of the variable name")
        elif args[0] == 'trace' and len(args) == 2:
            if (rule_1.match(args[1])):
                var = re.findall(r"([A-Za-z_][\w]*$)", args[1])
                var = var[0]
                idx = None
                ctxt.cmd_trace(var, idx)
            elif (rule_2.match(args[1])):
                var = re.findall(r"([A-Za-z_][\w]*)", args[1])
                var = var[0]
                idx = re.findall(r"(\[\d+\])", args[1])
                idx = idx[0]
                idx = int(idx[1:-1])
                ctxt.cmd_trace(var, idx)
            else:
                print("Invalid typing of the variable name")
        else:
            print("Invalid typing of the variable name")