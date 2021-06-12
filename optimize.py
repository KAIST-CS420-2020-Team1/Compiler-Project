import itertools
import functools

import parse
import analysis
import CFG

# Evaluate constant expression before running the code
# i.e. constant folding
def const_expr_eval(expr):
    if(isinstance(expr, parse.UniOp)):
        expr.operand = const_expr_eval(expr.operand)
        if(isinstance(expr.operand, parse.Const)):
            # Only + and - can be simplified
            if expr.op == '+':
                return expr.operand
            elif expr.op == '-':
                return parse.Const(- expr.operand.value)
        return expr
    elif(isinstance(expr, parse.BinOp)):
        expr.left = const_expr_eval(expr.left)
        expr.right = const_expr_eval(expr.right)
        if(isinstance(expr.left, parse.Const) and isinstance(expr.right, parse.Const)):
            return parse.Const(CFG.binop(expr.op, expr.left.value, expr.right.value))
        return expr
    elif(isinstance(expr, parse.Assign)):
        expr.lvalue = const_expr_eval(expr.lvalue)
        expr.rvalue = const_expr_eval(expr.rvalue)
        return expr
    elif(isinstance(expr, parse.ArrayIdx)): # L-value is not const
        expr.index = const_expr_eval(expr.index)
        return expr
    elif(isinstance(expr, parse.FuncCall)):
        expr.args = map(const_expr_eval, expr.args)
        return expr
    elif(isinstance(expr, parse.Identifier) or isinstance(expr, parse.Const)):
        return expr

def const_eval_in_stmt(stmt):
    if isinstance(stmt, parse.Statement):
        stmt.content = const_expr_eval(stmt.content)
    elif isinstance(stmt, parse.EachDecl) and stmt.value != None:
        stmt.value = const_expr_eval(stmt.value)
    # Otherwise(loops) it is handled in CFG-> No change (or print statement)
    return stmt



# List of variables used in l-value expr
def used_in_l_value(expr):
    if isinstance(expr, parse.UniOp): # Always '*'
        return used_in_l_value(expr.operand)
    elif isinstance(expr, parse.ArrayIdx):
        return used_in_l_value(expr.array) + used_in_expr(expr.index)
    elif isinstance(expr, parse.Identifier):
        return set() # Identifier is not used

# List of variables used in expr
def used_in_expr(expr):
    if(isinstance(expr, parse.UniOp)):
        # left side of ++, -- is used in value
        return used_in_expr(expr.operand)
    elif(isinstance(expr, parse.BinOp)):
        return used_in_expr(expr.left) + used_in_expr(expr.right)
    elif(isinstance(expr, parse.Assign)):
        if expr.op == '=':
            return used_in_l_value(expr.lvalue) + used_in_expr(expr.rvalue)
        else: # left side of +=, -= is used in value
            return used_in_expr(expr.lvalue) + used_in_expr(expr.rvalue)
    elif(isinstance(expr, parse.ArrayIdx)):
        return used_in_expr(expr.array) + used_in_expr(expr.index)
    elif(isinstance(expr, parse.FuncCall)):
        return set(itertools.chain(*map(used_in_expr, expr.args)))
    elif(isinstance(expr, parse.Identifier)):
        return { expr.name }
    elif(isinstance(expr, parse.Const)):
        return set()


# List of variables resulted via l-value expr, at most one result
def result_in_l_value(expr):
    if isinstance(expr, parse.UniOp): # Always '*'
        return result_in_l_value(expr.operand)
    elif isinstance(expr, parse.ArrayIdx):
        return result_in_l_value(expr.array)
    elif isinstance(expr, parse.Identifier):
        return { expr.name } # Identifier in l-value is resulted

# List of variables resulted(defined/modified) from expr
def result_of_expr(expr):
    if(isinstance(expr, parse.UniOp)):
        if expr.op in ['++', '--']:
            return result_in_l_value(expr.operand)
        return result_of_expr(expr.operand)
    elif(isinstance(expr, parse.BinOp)):
        return result_of_expr(expr.left) + result_of_expr(expr.right)
    elif(isinstance(expr, parse.Assign)):
        return result_in_l_value(expr.lvalue) + result_of_expr(expr.rvalue)
    elif(isinstance(expr, parse.ArrayIdx)):
        return result_of_expr(expr.array) + result_of_expr(expr.index)
    elif(isinstance(expr, parse.FuncCall)):
        return set(itertools.chain(*map(result_of_expr, expr.args)))
    elif(isinstance(expr, parse.Identifier)):
        return set() # Identifier is not resulted unless inside l-value
    elif(isinstance(expr, parse.Const)):
        return set()

# Substitute ident with to_sub
def substitute_expr(expr, ident, to_sub):
    if(isinstance(expr, parse.UniOp)):
        res = parse.UniOp(substitute_expr(expr.operand, ident, to_sub), expr.op)
        res.postfix = expr.postfix
        return res
    elif(isinstance(expr, parse.BinOp)):
        return parse.BinOp(substitute_expr(expr.left, ident, to_sub), substitute_expr(expr.right, ident, to_sub), expr.op)
    elif(isinstance(expr, parse.Assign)):
        return parse.Assign(substitute_expr(expr.lvalue, ident, to_sub), substitute_expr(expr.rvalue, ident, to_sub), expr.op)
    elif(isinstance(expr, parse.ArrayIdx)):
        return parse.ArrayIdx(substitute_expr(expr.array, ident, to_sub), substitute_expr(expr.index, ident, to_sub))
    elif(isinstance(expr, parse.FuncCall)): # TODO Consider Fn_Call_Stmt
        return list(itertools.chain(*map(functools.partial(substitute_expr, ident=ident, to_sub=to_sub), expr.args)))
    elif(isinstance(expr, parse.Identifier)):
        if expr.name == ident:
            return to_sub
        else:
            return expr
    elif(isinstance(expr, parse.Const)):
        return expr

def substitute_stmt(stmt, ident, to_sub):
    if(isinstance(stmt, parse.Statement)):
        stmt.content = substitute_expr(stmt.content, ident, to_sub)
        return stmt
    elif(isinstance(stmt, parse.EachDecl)):
        if stmt.value != None:
            stmt.value = substitute_expr(stmt.value, ident, to_sub)
        return stmt
    raise TypeError('Unexpected type', type(stmt))

UNIT_ITER = 8
UNROLL_THRESHOLD = 16


# Unroll loops of pattern: for(i = 0; i < v; i++)
### NOTE Not used
def unroll_loop(stmt):
    if(isinstance(stmt, parse.Iteration)):
        desc = stmt.loopDesc
        body = stmt.body.stmts
        if len(body) > UNROLL_THRESHOLD:
            return stmt
        if(isinstance(desc, parse.ForDesc)):
            # Initiation
            if not isinstance(desc.init, parse.Assign):
                return stmt
            if not desc.init.op == '=':
                return stmt
            if not isinstance(desc.init.lvalue, parse.Identifier):
                return stmt
            if not isinstance(desc.init.rvalue, parse.Const):
                return stmt
            if not isinstance(desc.init.rvalue.type, parse.Int):
                return stmt
            iterator = desc.init.lvalue.name
            initial = desc.init.rvalue.value

            # Condition
            if not isinstance(desc.until, parse.BinOp):
                return stmt
            if not desc.until.op in ["<", ">", "<=", ">="]:
                return stmt
            if not isinstance(desc.until.left, parse.Identifier):
                return stmt
            if not isinstance(desc.until.right, parse.Const):
                return stmt
            if not isinstance(desc.until.right.type, parse.Int):
                return stmt
            if desc.until.left.name != iterator:
                return stmt
            compare = desc.until.op
            final = desc.until.right.value

            # Iteration
            if not isinstance(desc.iter, parse.UniOp):
                return stmt
            if not desc.iter.op in ["++", "--"]:
                return stmt
            if not isinstance(desc.iter.operand, parse.Identifier):
                return stmt
            if desc.iter.operand.name != iterator:
                return stmt
            operator = desc.iter.op

            # No modification of iterator - Need handling on declaration
            for sub in body:
                if isinstance(sub, parse.EachDecl):
                    if sub.value != None and iterator in result_of_expr(sub.value):
                        return stmt
                elif isinstance(sub, parse.Statement):
                    if iterator in result_of_expr(sub.content):
                        return stmt
                else:
                    return stmt # Do not unroll when it has inner loops or conditionals

            if (compare in ["<", "<="] and operator == "--") or (compare in [">", ">="] and operator == "++"):
                print("Non-terminating behavior on {}".format(desc))
                raise ValueError("semantic error")
            if compare == "<=":
                final = final + 1
            elif compare == ">=":
                final = final - 1

            if operator == '++':
                until_op = '<'
                iter_op = '+='
            else:
                until_op = '>'
                iter_op = '-='

            trailing = (final - initial) % UNIT_ITER
            new_cond = parse.BinOp(parse.Identifier(iterator), parse.Const(final - trailing, parse.Int()), until_op)
            new_iter = parse.Assign(parse.Identifier(iterator), parse.Const(UNIT_ITER, parse.Int()), iter_op)
            new_desc = parse.ForDesc(desc.init, new_cond, new_iter)
            new_body = []
            for j in range(UNIT_ITER):
                on_ite = parse.BinOp(parse.Identifier(iterator), parse.Const(j, parse.Int())) # i + j
                new_body_j = map(functools.partial(substitute_stmt, ident=iterator, to_sub = on_ite), body)
                new_body = new_body + list(new_body_j)
            return parse.Iteration(new_desc, new_body)

    return stmt


class OptimData:
    def __init__(self):
        self.used = set()
        self.defed = set()
        self.var_in = set()
        self.var_out = set()

        self.per_line = list()

        self.initialized = False
        self.visited = False

# Calculates 'in' and 'out' variables and fills the information within each node
def calc_in_out(store: "dict[str, OptimData]", node: CFG.Node):
    nst = store[node.index]
    if not nst.initialized: # Updates the used/defined
        for stmt in node.block:
            nst_line = OptimData()
            nst.per_line.append(nst_line)
            if isinstance(stmt, parse.Statement):
                nst_line.used = used_in_expr(stmt.content)
                nst_line.defed = result_of_expr(stmt.content)
            elif isinstance(stmt, parse.EachDecl):
                nst_line.used = used_in_expr(stmt.value)
                nst_line.defed = result_of_expr(stmt.value)
            elif isinstance(stmt, analysis.Fn_Call_Stmt):
                for arg in stmt.args:
                    nst_line.used += used_in_expr(arg)
                    nst_line.defed += result_of_expr(arg)
            elif isinstance(stmt, parse.PrintStmt) and stmt.value != None:
                nst_line.used = used_in_expr(stmt.value)
                nst_line.defed = result_of_expr(stmt.value)
        if node.branch:
            nst_line = OptimData()
            nst.per_line.append(nst_line)
            nst_line.used = used_in_expr(node.pred)
            nst_line.defed = result_of_expr(node.pred)

        # Substitutes
        nst.used = set()
        nst.defed = set()
        for v in nst.per_line:
            nst.used += v.used
            nst.defed += v.defed
        nst.initialized = True

    var_out = set()
    var_in = set()
    nst.visited = True # Pre-mark visited, so lower calls won't call this fn again

    for next_node in node.next:
        # Does not visit to calculate again in loop case
        if not store[next_node.index].visited:
            calc_in_out(next_node)
        # Calculates for sub-nodes
        var_out += nst.var_in
    nst.var_out = var_out

    var_in = var_out
    for i in range(len(nst.per_line)-1, 0, -1):
        nst_line: OptimData = nst.per_line[i]
        nst_line.var_out = var_in # Succeeding IN is current OUT on linear
        nst_line.var_in = nst_line.used + var_out.difference(nst_line.defed)
        var_in = nst_line.var_in
    nst.var_in = var_in # 0-th index IN is the block IN

# Eliminates simple evaluations without assignments and side-effects
def eliminate_pure_expr(expr):
    if(isinstance(expr, parse.UniOp)):
        if expr.op in ['+', '-', '&']: # Pointer dereference is considered impure ()
            return eliminate_pure_expr(expr.operand)
    elif(isinstance(expr, parse.BinOp)):
        return eliminate_pure_expr(expr.left) + eliminate_pure_expr(expr.right)
    elif(isinstance(expr, parse.Assign)):
        return expr # Assignment is not pure
    elif(isinstance(expr, parse.ArrayIdx)):
        return expr # Consider array indexing as not pure, may cause exception
    elif(isinstance(expr, parse.FuncCall)):
        # Function call is not pure
        return expr
    elif(isinstance(expr, parse.Identifier) or isinstance(expr, parse.Const)):
        return [ ] # Identifier / Constant is pure

# Eliminate dead statement.
# Dead code is an assignment which results in non-output variables.
# Currently does not account for stuffs nested inside for complexity reasons (e.g. inside pred)
def eliminate_dead_stmt(out: "set[str]", stmt):
    if isinstance(stmt, parse.Statement) and not stmt.returning:
        expr = stmt.content
        if isinstance(expr, parse.Assign):
            stmt_out = result_in_l_value(expr.lvalue)
            if stmt_out.isdisjoint(out):
                return eliminate_dead_stmt(out, expr.rvalue)
            else:
                return [ stmt ]
        else: # When not assignments
            effs = list(map(parse.Statement, eliminate_pure_expr(expr)))
            for eff in effs:
                eff.set_line(stmt.line_num)
            return effs
    elif isinstance(stmt, parse.EachDecl):
        if stmt.name in out or stmt.value == None:
            return [ stmt ]
        else:
            decl = parse.EachDecl(stmt.type, stmt.name)
            decl.set_line(stmt.line_num)
            return [ decl ] + eliminate_dead_stmt(out, stmt.value)
    elif isinstance(stmt, parse.PrintStmt):
        return [ stmt ]

# Eliminate dead code within this and successor nodes. Mutates CFG.
# Does not change branch condition, for it can cause anomalies
def eliminate_dead(store: "dict[str, OptimData]", node: CFG.Node):
    new_block = list()
    i = 0
    for stmt in node.block: # Finds corresponding information
        new_stmt = eliminate_dead_stmt(store[node.index].per_line[i].var_out, stmt)
        new_block.extend(new_stmt)
        i = i + 1
    node.block = new_block
    store[node.index].visited = True
    for next_node in node.next:
        if not store[next_node.index].visited:
            eliminate_dead(store, next_node)

# Simple two-pass dead-code elimination
# Currently, does not eliminate dead code caused by eliminating the previous dead code
def dead_code_elimination(node: CFG.Node):
    store = dict()
    store.setdefault(OptimData())
    calc_in_out(store, node) # First pass
    for v in store.values:
        v.visited = False
    calc_in_out(store, node) # Second pass, to detect for loops
    for v in store.values:
        v.visited = False
    eliminate_dead(store, node)


def const_eval_each(visited:"dict[str, bool]", node: CFG.Node):
    visited[node.index] = True
    node.block = list(map(const_eval_in_stmt, node.block))
    if node.pred != None:
        node.pred = const_expr_eval(node.pred)
    for next_node in node.next:
        if not visited[next_node.index]:
            const_eval_each(visited, next_node)
# Constant evaluation in CFG. Mutates CFG
def const_eval_node(node: CFG.Node):
    visited = dict()
    visited.setdefault(False)
    const_eval_each(visited, node)
