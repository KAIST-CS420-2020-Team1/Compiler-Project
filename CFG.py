import parse
import operator
import copy
import re
from stack import *
from structure import *

node_index = 0


value_stack = ValueStack()
call_stack = CallStack()
function_table = Function_Table()


class Node:
    def __init__(self, block, line_list, pred=None):
        global node_index
        self.index = node_index
        node_index += 1
        self.prev = []
        self.next = []

        self.block = block
        self.pred = pred
        self.line_list = line_list
        self.cursor = 0

        self.branch = False

    def insert_next(self, node):
        self.next.append(node)
        node.prev.append(self)
        if len(self.next) > 1:
            self.branch = True

    def insert_prev(self, node):
        self.prev.append(node)
        node.next.append(self)

    def get_next(self):
        return self.next

    def get_prev(self):
        return self.prev

    def get_line_list(self):
        return self.line_list

    def get_line(self, num):
        return self.block[num]

    def find_prev_branch(self):
        pass

    def next_line(self):
        node = self
        if len(node.block) != 0:
            evaluate(0, node.get_line(node.cursor))
            if node.cursor < (len(node.block) -1):
                node.cursor += 1
                return node
            else:
                node.cursor = 0
                if node.branch:
                    # for i, pred in enumerate(self.pred):
                    #     if evaluate(pred):
                    #         next = self.get_next()[i]
                    #         return next, next.get_line(self.get_line_list()[0]), self.get_line_list()[0]
                    # raise Exception("no true branch")
                    if evaluate(0, node.pred): # Ideally, substitution should not be here
                        next = node.get_next()[0]
                        return next
                    else:
                        next = node.get_next()[1]
                        return next
                else:
                    if len(node.get_next()) > 0:
                        next = node.get_next()[0]
                        return next
                    else:
                        return None
        else:
            if node.branch:
                # for i, pred in enumerate(self.pred):
                #     if evaluate(pred):
                #         next = self.get_next()[i]
                #         return next, next.get_line(self.get_line_list()[0]), self.get_line_list()[0]
                # raise Exception("no true branch")
                if evaluate(0, node.pred):  # Ideally, substitution should not be here
                    next = node.get_next()[0]
                else:
                    next = node.get_next()[1]
            else:
                if len(node.get_next()) > 0:
                    next = node.get_next()[0]
                else:
                    return None
            return next.next_line()


def binop(op, lhs, rhs):
    operations = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv, '<': operator.lt, '>': operator.gt, '==': operator.eq}
    return operations[op](lhs, rhs)


def evaluate(line, expr):
    cur_fun_name = call_stack.called[0].name
    cur_fun_table = function_table.table[cur_fun_name]
    cur_symbol_table = cur_fun_table.ref_sym
    cur_value_table = cur_fun_table.ref_value

    if isinstance(expr, parse.Statement) and expr.returning:
        # return something;
        return_value = evaluate(expr.line_num, expr.content)
        cur_fun_table.return_value = return_value
        call_stack.ret()
        # cur_symbol_table = function_table.get_symbom_table(some_func)
        return None
    else:
        if isinstance(expr, parse.Statement):
            line = expr.line_num
            expr = expr.content

        # if isinstance(expr, parse.FunctionDefn):
        #     fun_name = expr.declarator.base
        #     fun_type = expr.r_type
        #     params = []
        #     p_types = []
        #
        #     symbol_table = Symbol_Table(None)
        #     value_table = ValueTable()
        #
        #     for p in expr.declarator.params:
        #         p_type = p.base_type
        #         p_name = p.decl_assigns
        #         p_types.append(p_type)
        #         symbol_table.insert(p_name, p_type, None)
        #
        #     body = expr.body
        #
        #     function_table.insert(fun_name, fun_type, p_types, 1, body, symbol_table)
        if isinstance(expr, parse.Declaration):
            variables = expr.decl_assigns
            var_type = expr.base_type.type
            # int a; no declaration with init value.
            for variable in variables:
                var_name = variable.name
                cur_symbol_table.insert(var_name, var_type, 1)
                cur_value_table.allocate_local(var_name, None, expr.line_num)
            return None
        elif isinstance(expr, parse.Assign):
            # a = 2;
            var_name = expr.lvalue.name
            p = re.compile(r"(.+)\[(.+)\]")
            m = p.match(var_name)
            if m != None:
                var_name = m.group(1)
                var_length = m.group(2)
            else:
                var_length = 1
            _op = expr.op
            value = evaluate(line, expr.rvalue)
            # type check needed

            #
            if value != None:
                cur_value_table.set_value(var_name, value, line)
            return None
        elif isinstance(expr, parse.Identifier):
            # variable: a
            return cur_value_table.get_value(expr.name)
        elif isinstance(expr, parse.Const):
            # const: 3
            return expr.value
        elif isinstance(expr, parse.BinOp):
            # a + b
            lhs = evaluate(line, expr.left)
            rhs = evaluate(line, expr.right)
            op = expr.op
            return binop(op, lhs, rhs)
        elif isinstance(expr, parse.UniOp):
            # only a++?
            if expr.op == '++':
                operand = evaluate(line, expr.operand)
                value = binop('+', operand, 1)
                cur_value_table.set_value(expr.operand.name, value, line)
                return binop('+', operand, 1)
            elif expr.op == '-' and not expr.postfix:
                operand = -1 * evaluate(line, expr.operand)
                return operand
            elif expr.op == '+' and not expr.postfix:
                operand = evaluate(line, expr.operand)
                return operand
            raise Exception("not implemented uniop")
            # op = expr.op
        elif isinstance(expr, parse.FuncCall):
            # some_func(x, y)
            fn_name = expr.fn_name.name
            fun_params = function_table.table[fn_name].p_name
            fun_args = expr.args

            for param, arg in zip(fun_params, fun_args):
                function_table.table[fn_name].ref_value.set_value(param, evaluate(line, arg), line)

            if function_table.table[fn_name].return_value == None:
                call_stack.link(CallContext(fn_name, line))
            else:
                return_value = function_table.table[fn_name].return_value
                function_table.table[fn_name].return_value = None
                return return_value
            return None  # ??
        elif isinstance(expr, parse.Body):
            return_value = None
            for stmt in expr.stmts:
                if stmt.returning:
                    return_value = evaluate(stmt.line_num, stmt)
                else:
                    evaluate(stmt.line_num, stmt)
            return return_value
        elif isinstance(expr, parse.PrintStmt):
            format = expr.format
            value = evaluate(line, expr.value)
            if value != None:
                print(format %(value))
            else:
                if "%d" in format or "%f" in format:
                    raise Exception("formatting error")
                else:
                    print(format)
            return None
    return None


def get_pred(stmt):
    if isinstance(stmt, parse.Selection):
        return stmt.cond
    elif isinstance(stmt, parse.Iteration):
        if isinstance(stmt.loopDesc, parse.ForDesc):
            return stmt.loopDesc.until
        else:
            return stmt.loopDesc


def get_branch(stmt):
    if stmt.hasElse:
        return [stmt.thenB, stmt.elseB]
    else:
        return [stmt.thenB]


def generate_graph(ast):
    block = []
    line_list = []
    pred = []
    root = Node(copy.deepcopy(block), copy.deepcopy(line_list), copy.deepcopy(pred))
    last_nodes = [root]

    if isinstance(ast, parse.TranslationUnit):
        for decl in ast.decls:
            if isinstance(decl, parse.FunctionDefn):
                fun_name = decl.declarator.base.name
                fun_type = decl.r_type.type
                params = []
                p_types = []
                p_names = []

                symbol_table = Symbol_Table(None)
                value_table = ValueTable()

                for p in decl.declarator.params:
                    p_type = p.base_type
                    p_name = p.desugar()[0].name
                    p_types.append(p_type)
                    p_names.append(p_name)
                    symbol_table.insert(p_name, p_type, None)
                    value_table.allocate_local(p_name, None, decl.line_num)

                body = decl.body

                function_table.insert(fun_name, fun_type, p_types, p_names, 1, body, symbol_table, value_table, None)
                if fun_name == 'main':
                    ast = body
                    call_stack.link(CallContext(fun_name, 1))
            else:
                pass

    # if isinstance(expr, parse.TranslationUnit):
    #     body = function_table.find('main')
    # else:
    #     body = ast

    for stmt in ast.stmts:
        if not isinstance(stmt, parse.Selection) and not isinstance(stmt, parse.Iteration) and not (isinstance(stmt, parse.Statement) and isinstance(stmt.content, parse.FuncCall)) and not (isinstance(stmt, parse.Statement) and isinstance(stmt.content, parse.Assign) and isinstance(stmt.content.rvalue, parse.FuncCall)):
            block.append(stmt)
            # line_list.append(line)
        elif isinstance(stmt, parse.Iteration):
            for_init = stmt.loopDesc.init
            init_stmt = parse.Statement(for_init)
            init_stmt.set_line(stmt.line_num)
            block.append(init_stmt)

            pred = get_pred(stmt)  # [true_pred, false_pred]
            node = Node(copy.deepcopy(block), copy.deepcopy(line_list), copy.deepcopy(pred))

            for last_node in last_nodes:
                last_node.insert_next(node)
            last_nodes = [node]

            block = []
            line_list = []

            branch_last_node = []

            # for br in get_branch(stmt):  # br = body
            #     br_node, br_last_node = generate_graph(br)  # for nested branch
            #     last_nodes[0].insert_next(br_node)
            #     branch_last_node += br_last_node

            for_iter = stmt.loopDesc.iter

            iter_stmt = parse.Statement(for_iter)
            iter_stmt.set_line(stmt.line_num)

            body = stmt.body
            body.stmts.append(iter_stmt)
            loop_node, loop_last_node = generate_graph(body)

            loop_end_node = Node([], [], copy.deepcopy(pred))
            loop_last_node[0].insert_next(loop_end_node)
            last_nodes.append(loop_end_node)
            pred = []
            for last_node in last_nodes:
                last_node.insert_next(loop_node)
        elif isinstance(stmt, parse.Statement) and isinstance(stmt.content, parse.FuncCall):
            block.append(stmt)
            node = Node(copy.deepcopy(block), copy.deepcopy(line_list), copy.deepcopy(pred))

            for last_node in last_nodes:
                last_node.insert_next(node)
            last_nodes = [node]

            block = []
            line_list = []

            fun_name = stmt.content.fn_name.name
            # fun_args = stmt.content.args
            #
            # fun_params = function_table.table[fun_name].p_name

            # for param, arg in zip(fun_params, fun_args):
            #     function_table.table[fun_name].ref_value.set_value(param, evaluate(arg), 1)

            body = function_table.table[fun_name].body

            call_node, call_last_node = generate_graph(body)

            last_nodes[0].insert_next(call_node)
            last_nodes = call_last_node
        elif isinstance(stmt, parse.Statement) and isinstance(stmt.content, parse.Assign) and isinstance(stmt.content.rvalue, parse.FuncCall):
            block.append(stmt)
            node = Node(copy.deepcopy(block), copy.deepcopy(line_list), copy.deepcopy(pred))

            for last_node in last_nodes:
                last_node.insert_next(node)
            last_nodes = [node]

            block = []
            line_list = []

            fun_name = stmt.content.rvalue.fn_name.name
            # fun_args = stmt.content.rvalue.args
            #
            # fun_params = function_table.table[fun_name].p_name

            # for param, arg in zip(fun_params, fun_args):
            #     function_table.table[fun_name].ref_value.set_value(param, evaluate(arg), 1)

            body = function_table.table[fun_name].body

            call_node, call_last_node = generate_graph(body)

            last_nodes[0].insert_next(call_node)
            last_nodes = call_last_node
            block = [stmt]
        else:  # if branch
            pred = get_pred(stmt)
            node = Node(copy.deepcopy(block), copy.deepcopy(line_list), copy.deepcopy(pred))

            for last_node in last_nodes:
                last_node.insert_next(node)
            last_nodes = [node]

            block = []
            line_list = []
            pred = []
            br_last_nodes = []

            for br in get_branch(stmt):  # br = body
                br_node, br_last_node = generate_graph(br)  # for nested branch
                last_nodes[0].insert_next(br_node)
                br_last_nodes += br_last_node
            if len(get_branch(stmt)) < 2:
                br_last_nodes += last_nodes
            last_nodes = br_last_nodes

    node = Node(copy.deepcopy(block), copy.deepcopy(line_list), copy.deepcopy(pred))
    for last_node in last_nodes:
        last_node.insert_next(node)
    last_nodes = [node]
    return root.get_next()[0], last_nodes