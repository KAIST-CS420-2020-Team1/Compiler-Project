import parse
import operator


class Node:
    def __init__(self, block, line_list, pred=[]):
        self.index = -1
        self.prev = []
        self.next = []

        self.block = block
        self.pred = pred
        self.line_list = line_list

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
        return self.block[self.line_list.index(num)]

    def find_prev_branch(self):
        pass

    def next_line(self, cur):
        eval(self.get_line(cur))
        if cur != max(self.get_line_list()):
            return self, self.get_line(cur+1), cur+1
        else:
            if self.branch:
                for i, pred in enumerate(self.pred):
                    if evaluate(pred):
                        next = self.get_next()[i]
                        return next, next.get_line(self.get_line_list()[0]), self.get_line_list()[0]
                raise Exception("no true branch")
            else:
                next = self.get_next()[0]
                return next, next.get_line(self.get_line_list()[0]), self.get_line_list()[0]


def binop(op, lhs, rhs):
    operations = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv, '<': operator.lt, '>': operator.gt}
    return operations[op](lhs, rhs)


def evaluate(expr):
    if expr.returning:
        # return something;
        return_value = evaluate(expr.content)
        call_stack.pop()
        cur_symbol_table = function_table.get_symbom_table(some_func)
        return return_value
    else:
        expr = expr.content
        if isinstance(expr, parse.FunctionDefn):
            fun_name = expr.declarator.base
            fun_type = expr.r_type
            params = []

            symbol_table = ...

            for p in expr.declarator.params:
                p_type = p.base_type
                p_name = p.decl_assigns
                symbol_table.add(p_name, p_type, None)

            funtion_table.add()
        if isinstance(expr, parse.Declaration):
            variables = expr.decl_assigns
            var_type = expr.base_type
            # int a; no declaration with init value.
            for variable in variables:
                symbol_table.add(variable, var_type, None)
            return None
        # elif is_assign:
        #     # a = 2;
        #     variable = expr.left
        #     value = evaluate(expr.right)
        #     # type check needed
        #     symbol_table.update(variable, value)
        #     return None
        # elif is_var:
        #     # variable: a
        #     return symbol_table.find(expr.name)
        elif isinstance(expr, parse.Const):
            # const: 3
            return expr.value
        elif isinstance(expr, parse.BinOp):
            # a + b
            lhs = evaluate(expr.left)
            rhs = evaluate(expr.right)
            op = expr.op
            return binop(op, lhs, rhs)
        elif isinstance(expr, parse.UniOp):
            # only a++?
            operand = evaluate(expr.operand)
            # op = expr.op
            return binop('+', operand, 1)
        elif isinstance(expr, parse.FuncCall):
            # some_func(x, y)
            fn_name = expr.fn_name
            args = expr.args
            call_stack.insert(fn_name, args)
            ############
            # execute function?
            # return_value = evaluate(function_table.get_body(fn_name))
            ############
            cur_symbol_table = function_table.get_symbom_table(fn_name)
            return None  # ??
        elif isinstance(expr, parse.Body):
            return_value = None
            for stmt in expr.stmts:
                if stmt.returning:
                    return_value = evaluate(stmt)
                else:
                    evaluate(stmt)
            return return_value
    return None


def get_pred(stmt):
    if isinstance(stmt, parse.Selection):
        return stmt.cond
    elif isinstance(stmt, parse.Iteration):
        if isinstance(stmt.loopDesc, parse.ForDesc):
            return stmt.loopDesc.until
        else:
            return stmt.loopDesc


def generate_graph(ast):
    block = []
    line_list = []
    pred = []
    root = Node(block, line_list, pred)
    last_nodes = [root]
    for decl in ast.decls:
        evaluate(decl)
        pass

    body = None
    body = ast.decls[0].body
    # if isinstance(expr, parse.TranslationUnit):
    #     body = function_table.find('main')
    # else:
    #     body = ast

    for stmt in body.stmts:
        if not isinstance(stmt, parse.Selection) and not isinstance(stmt, parse.Iteration):
            block.append(stmt)
            # line_list.append(line)
        elif is_loop(stmt):
            pred = get_loop_pred(stmt)  # [true_pred, false_pred]
            node = Node(block, line_list, pred)

            for last_node in last_nodes:
                last_node.insert_next(node)
            last_nodes = [node]

            block = []
            line_list = []
            pred = []
            branch_last_node = []

            # for br in get_branch(stmt):  # br = body
            #     br_node, br_last_node = generate_graph(br)  # for nested branch
            #     last_nodes[0].insert_next(br_node)
            #     branch_last_node += br_last_node

            body = stmt.body
            loop_node, loop_last_node = generate_graph(body)

            loop_end_node = Node([], [], pred)
            loop_last_node.insert_next(loop_end_node)

            for last_node in last_nodes:
                last_node.insert_next(loop_node)
            last_nodes.append(loop_end_node)

        else:  # if branch
            pred = get_pred(stmt)
            node = Node(block, line_list, pred)

            for last_node in last_nodes:
                last_node.insert_next(node)
            last_nodes = [node]

            block = []
            line_list = []
            pred = []
            br_last_nodes = []

            for br in get_branch(stmt): # br = body
                br_node, br_last_node = generate_graph(br) # for nested branch
                last_nodes[0].insert_next(br_node)
                br_last_nodes += br_last_node
            last_nodes = br_last_nodes

    node = Node(block, line_list, pred)
    for last_node in last_nodes:
        last_node.insert_next(node)
    last_nodes = [node]
    return root, last_nodes
