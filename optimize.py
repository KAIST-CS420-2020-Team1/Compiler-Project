import parse

# Evaluate constant expression before running the code
def const_expr_eval(expr):
    if(isinstance(expr, parse.UniOp)):
        # No unitary operation require .
        expr.operand = const_expr_eval(expr.operand)
        return expr
    elif(isinstance(expr, parse.BinOp)):
        expr.left = const_expr_eval(expr.left)
        expr.right = const_expr_eval(expr.right)
        if(isinstance(expr.left, parse.Const) and isinstance(expr.right, parse.Const)):
            # TODO Have a utility for running expression
            pass
        return expr
    elif(isinstance(expr, parse.ArrayIdx)): # L-value is not const
        expr.index = const_expr_eval(expr.index)
        return expr
    elif(isinstance(expr, parse.FuncCall)):
        expr.args = map(const_expr_eval, expr.args)
        return expr
    elif(isinstance(expr, parse.Identifier) or isinstance(expr, parse.Const)):
        return expr
    else:
        raise TypeError("Illegal type", type(expr))

# Unroll loops of pattern: for(i = 0; i < 100; i++)
def unroll_loop(stmt):
    if(isinstance(stmt, parse.Iteration)):
        desc = stmt.loopDesc
        body = stmt.body.decls + stmt.body.stmts
        # TODO Heuristics for enabling? E.g. when short
        if(isinstance(desc, parse.ForDesc)):
            # TODO Perhaps analyze flow of values
            # Initiation
            if not isinstance(desc.init, parse.BinOp):
                return stmt
            if not desc.init.op == '=':
                return stmt
            if not isinstance(desc.init.left, parse.Identifier):
                return stmt
            if not isinstance(desc.init.right, parse.Const):
                return stmt
            if not isinstance(desc.init.right.type, parse.Int):
                return stmt
            iterator = desc.init.left.name
            initial = desc.init.right.value

            # Condition
            # TODO Invert order
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

            # TODO Inspect body for changes of i
            # TODO Replace i & concat

            if (compare in ["<", "<="] and operator == "--") or (compare in [">", ">="] and operator == "++"):
                print("Nonterminating behavior on {}".format(desc))
                raise ValueError("semantic error")
            if compare == "<=":
                final = final + 1
            elif compare == ">=":
                final = final - 1

            if operator == "++":
                unit_iter = 8
                trailing = (final - initial) % unit_iter
                new_cond = parse.BinOp(parse.Identifier(iterator), parse.Const(final - trailing, parse.Int()), "<")
                new_iter = parse.BinOp(parse.Identifier(iterator), parse.Const(unit_iter, parse.Int()), "+=")
                new_desc = parse.ForDesc(desc.init, new_cond, new_iter)
                # TODO body transformation
                return parse.Iteration(new_desc, body)

    return stmt

# Do if time allows
def condition_simplify(stmt):
    0

