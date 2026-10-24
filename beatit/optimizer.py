"""Phase 5: deliberately small, readable IR optimization passes."""
from copy import deepcopy
from ast_nodes import BinOp, Num, UnaryMinus
from ir import *


class Optimizer:
    """Performs constant folding and removes statically unreachable statements."""
    def optimize(self, program):
        result = deepcopy(program)
        result.globals = self.block(result.globals)
        for function in result.functions:
            function.body = self.block(function.body)
        return result

    def expression(self, expr):
        if isinstance(expr, UnaryMinus):
            expr.operand = self.expression(expr.operand)
            return Num(-expr.operand.value, expr.line) if isinstance(expr.operand, Num) else expr
        if isinstance(expr, BinOp):
            expr.left, expr.right = self.expression(expr.left), self.expression(expr.right)
            if isinstance(expr.left, Num) and isinstance(expr.right, Num):
                left, right = expr.left.value, expr.right.value
                try:
                    value = {"+": lambda: left + right, "-": lambda: left - right,
                             "*": lambda: left * right, "/": lambda: left / right,
                             "<": lambda: left < right, ">": lambda: left > right,
                             "<=": lambda: left <= right, ">=": lambda: left >= right,
                             "==": lambda: left == right, "!=": lambda: left != right}[expr.op]()
                    return Num(int(value) if isinstance(value, bool) else value, expr.line)
                except ZeroDivisionError:
                    return expr
        return expr

    def block(self, statements):
        kept = []
        for statement in statements:
            if isinstance(statement, (IRAssign, IRAugAssign)):
                statement.value = self.expression(statement.value)
            elif isinstance(statement, IRWhile):
                statement.condition = self.expression(statement.condition)
                statement.body = self.block(statement.body)
                if isinstance(statement.condition, Num) and not statement.condition.value:
                    continue
            elif isinstance(statement, IRFor):
                statement.body = self.block(statement.body)
            elif isinstance(statement, (IRPlay, IRSleep, IRReturn)):
                for name in ("beat", "amount", "value", "start", "end"):
                    value = getattr(statement, name, None)
                    if value is not None: setattr(statement, name, self.expression(value))
            kept.append(statement)
            if isinstance(statement, IRReturn):
                break
        return kept
