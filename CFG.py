import os


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
        if cur != max(self.get_line_list()):
            return self, self.get_line(cur+1)
        else:
            if self.branch:
                for i, pred in enumerate(self.pred):
                    if is_true(evaluate(pred)):
                        next = self.get_next()[i]
                        return next, next.get_line(self.get_line_list()[0])
                raise Exception("no true branch")
            else:
                next = self.get_next()[0]
                return next, next.get_line(self.get_line_list()[0])

class Block:
    def __init__(self):
        pass

    def evaluate(self, expr):
        if is_decl:
            variable = ...
            var_type = ...
            # int a; no declaration with init value.
            symbol_table.add(variable, var_type, None)
            pass
        elif is_assign:
            # a = 2;
            variable = ...
            value = evaluate(...)
            symbol_table.update(variable, value)
            pass
        elif is_var:
            # variable: a
            return symbol_table.find(expr)
        elif is_const:
            # const: 3
            return get_num(expr)
        elif is_binary:
            # a + b
            lhs = ...
            rhs = ...
            op = ...
            return op(evaluate(lhs), evaluate(rhs))
        elif is_unary:
            # a++
            operand = ...
            op = ...
            return op(evaluate(operand))

        elif is_call:
            # some_func(x, y)
            pass
        elif is_return:
            # return something;
            pass


def generate_graph(ast):
    root = Node()
    last_nodes = [root]
    block = []
    line_list = []
    pred = []
    for stmt, line in ast:
        if not is_branch(stmt) and not is_loop(stmt):
            block.append(stmt)
            line_list.append(line)
        elif is_loop(stmt):
            pred = get_loop_pred(stmt)
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

            body = get_body(stmt)
            loop_node, loop_last_node = generate_graph(body)

        else:
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

            block = []
            line_list = []
            pred = []

    return root, last_nodes
