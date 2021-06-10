import itertools
import functools

import parse
import CFG

# Evaluate constant expression before running the code
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
        return [] # Identifier is not used

# List of variables used in expr
def used_in_expr(expr):
    if(isinstance(expr, parse.UniOp)):
        if expr.op in ['++', '--']:
            return used_in_l_value(expr.operand)
        else:
            return used_in_expr(expr.operand)
    elif(isinstance(expr, parse.BinOp)):
        return used_in_expr(expr.left) + used_in_expr(expr.right)
    elif(isinstance(expr, parse.Assign)):
        return used_in_l_value(expr.lvalue) + used_in_expr(expr.rvalue)
    elif(isinstance(expr, parse.ArrayIdx)):
        return used_in_expr(expr.array) + used_in_expr(expr.index)
    elif(isinstance(expr, parse.FuncCall)):
        return list(itertools.chain(*map(used_in_expr, expr.args)))
    elif(isinstance(expr, parse.Identifier)):
        return [ expr.name ]
    elif(isinstance(expr, parse.Const)):
        return []


# List of variables resulted via l-value expr
def result_in_l_value(expr):
    if isinstance(expr, parse.UniOp): # Always '*'
        return result_in_l_value(expr.operand)
    elif isinstance(expr, parse.ArrayIdx):
        return result_in_l_value(expr.array)
    elif isinstance(expr, parse.Identifier):
        return [ expr.name ] # Identifier in l-value is resulted

# List of variables resulted from expr
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
        return list(itertools.chain(*map(result_of_expr, expr.args)))
    elif(isinstance(expr, parse.Identifier)):
        return [] # Identifier is not resulted unless inside l-value
    elif(isinstance(expr, parse.Const)):
        return []

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
    elif(isinstance(expr, parse.FuncCall)): # Consider Fn_Call_Stmt
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
# TODO Perform on CFG
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

# Eliminates the dead code
# TODO Require CFG
def dead_code_elimination():
    pass
