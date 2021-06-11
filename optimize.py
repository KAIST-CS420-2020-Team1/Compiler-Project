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
            # TODO utility for running expression
            pass
        return expr
    elif(isinstance(expr, parse.BinOp)):
        expr.left = const_expr_eval(expr.left)
        expr.right = const_expr_eval(expr.right)
        if(isinstance(expr.left, parse.Const) and isinstance(expr.right, parse.Const)):
            return parse.Const(CFG.binop(expr.op, expr.left, expr.right))
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
# TODO Maybe perform on CFG
def unroll_loop(stmt):
    if(isinstance(stmt, parse.Iteration)):
        desc = stmt.loopDesc
        body = stmt.body.stmts
        if len(body) > UNROLL_THRESHOLD:
            return stmt
        if(isinstance(desc, parse.ForDesc)):
            # TODO Perhaps analyze flow of values
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


# TODO Obtain some kind of "id" for each node, and use a table over it
# Calculates 'in' and 'out' variables and fills the information within each node
def calc_in_out(node: CFG.Node):
    used = set() # Used
    defed = set() # Defined/Modified
    # TODO Better tracking of used / defed in a block
    for stmt in node.block:
        if isinstance(stmt, parse.Statement):
            used += used_in_expr(stmt.content)
            defed += result_of_expr(stmt.content)
        elif isinstance(stmt, parse.EachDecl):
            used += used_in_expr(stmt.value)
            defed += result_of_expr(stmt.value)
        elif isinstance(stmt, analysis.Fn_Call_Stmt):
            for arg in stmt.args:
                used += used_in_expr(arg)
                defed += result_of_expr(arg)
        # TODO Consider Iteration and Condition representation

    node.var_in = set()
    node.var_out = set()
    for next_node in node.next:
        # Calculates for sub-nodes
        calc_in_out(next_node) # TODO Handle loops
        node.var_out += next_node.var_in
        node.var_in = used + node.var_out.difference(defed)

# Eliminates simple evaluations without assignments and side-effects
def eliminate_pure_expr(expr):
    if(isinstance(expr, parse.UniOp)):
        if expr.op in ['+', '-', '&']:
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
# Currently does not account for stuffs nested inside for complexity reasons
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
        if stmt.name in out:
            return [ stmt ]
        else:
            return [ parse.EachDecl(stmt.type, stmt.name)
                ] + eliminate_dead_stmt(out, stmt.value)

# Eliminate dead code within this and successor nodes
def eliminate_dead(node: CFG.Node):
    mapped = map(functools.partial(eliminate_dead_stmt, node.var_out), node.block)
    node.block = list(filter(lambda s: s != None, itertools.chain(*mapped)))
    for next_node in node.next:
        eliminate_dead(next_node) # TODO Handle loops

# Simple two-pass dead-code elimination
# Currently, does not eliminate dead code caused by eliminating the previous dead code
def dead_code_elimination(node: CFG.Node):
    calc_in_out(node)
    eliminate_dead(node)
    
