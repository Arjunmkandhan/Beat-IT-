"""Phase 4: a small, inspectable intermediate representation for Beat It."""
from dataclasses import dataclass
from ast_nodes import *


@dataclass
class IRProgram:
    globals: list
    functions: list


@dataclass
class IRFunction:
    name: str
    params: list
    body: list
    return_type: str = "void"


@dataclass
class IRAssign:
    name: str
    value: object


@dataclass
class IRAugAssign:
    name: str
    op: str
    value: object


@dataclass
class IRPlay:
    beat: object
    start: object = None
    end: object = None
    unit: str = None
    is_async: bool = False


@dataclass
class IRSleep:
    amount: object
    unit: str = None


@dataclass
class IRFor:
    variable: str
    iterable: object
    body: list


@dataclass
class IRWhile:
    condition: object
    body: list


@dataclass
class IRReturn:
    value: object = None


@dataclass
class IRCall:
    call: object


@dataclass
class IRVolume:
    value: object


class IRGenerator:
    """Lower the AST into a backend-neutral statement representation."""
    def generate(self, program):
        functions, globals_ = [], []
        for statement in program.body:
            if isinstance(statement, (Import,)):
                continue
            if isinstance(statement, Volume):
                globals_.append(IRVolume(statement.value))
            elif isinstance(statement, FuncDef):
                functions.append(IRFunction(statement.name, statement.params,
                                            self.block(statement.body), statement.ret_type))
            else:
                globals_.append(self.statement(statement))
        return IRProgram(globals_, functions)

    def block(self, statements):
        return [self.statement(statement) for statement in statements]

    def statement(self, statement):
        if isinstance(statement, Assign):
            return IRAssign(statement.name, statement.value)
        if isinstance(statement, AugAssign):
            return IRAugAssign(statement.name, statement.op, statement.value)
        if isinstance(statement, Play):
            return IRPlay(statement.beat, statement.start, statement.end, statement.unit, statement.is_async)
        if isinstance(statement, Sleep):
            return IRSleep(statement.amount, statement.unit)
        if isinstance(statement, For):
            return IRFor(statement.var, statement.iterable, self.block(statement.body))
        if isinstance(statement, While):
            return IRWhile(statement.cond, self.block(statement.body))
        if isinstance(statement, Return):
            return IRReturn(statement.value)
        if isinstance(statement, CallStmt):
            return IRCall(statement.call)
        raise TypeError(f"Cannot lower {type(statement).__name__}")


def format_expr(expr):
    """Stable, source-like expression rendering used in --ir output."""
    if isinstance(expr, Num): return str(expr.value)
    if isinstance(expr, Str): return repr(expr.value)
    if isinstance(expr, Var): return expr.name
    if isinstance(expr, Qualified): return f"{expr.module}.{expr.sound}"
    if isinstance(expr, ListLit): return "[" + ", ".join(format_expr(x) for x in expr.items) + "]"
    if isinstance(expr, Range): return f"range({format_expr(expr.count)})"
    if isinstance(expr, Index): return f"{format_expr(expr.target)}[{format_expr(expr.index)}]"
    if isinstance(expr, Call): return f"{expr.name}(" + ", ".join(format_expr(x) for x in expr.args) + ")"
    if isinstance(expr, UnaryMinus): return "-" + format_expr(expr.operand)
    if isinstance(expr, BinOp): return f"({format_expr(expr.left)} {expr.op} {format_expr(expr.right)})"
    return repr(expr)


def format_ir(ir, indent=""):
    lines = []
    def body(statements, prefix):
        for item in statements:
            if isinstance(item, IRAssign): lines.append(f"{prefix}{item.name} = {format_expr(item.value)}")
            elif isinstance(item, IRAugAssign): lines.append(f"{prefix}{item.name} {item.op}= {format_expr(item.value)}")
            elif isinstance(item, IRPlay):
                p_cmd = "PLAY_ASYNC" if item.is_async else "PLAY"
                opts = f", {format_expr(item.start)}, {format_expr(item.end)}, {item.unit}" if item.start else ""
                lines.append(f"{prefix}{p_cmd} {format_expr(item.beat)}{opts}")
            elif isinstance(item, IRSleep): lines.append(f"{prefix}SLEEP {format_expr(item.amount)} {item.unit or 'ms'}")
            elif isinstance(item, IRCall): lines.append(f"{prefix}CALL {format_expr(item.call)}")
            elif isinstance(item, IRReturn): lines.append(f"{prefix}RETURN {format_expr(item.value) if item.value else ''}")
            elif isinstance(item, IRVolume): lines.append(f"{prefix}VOLUME {format_expr(item.value)}")
            elif isinstance(item, IRFor):
                lines.append(f"{prefix}FOR {item.variable} IN {format_expr(item.iterable)}:"); body(item.body, prefix + "  ")
            elif isinstance(item, IRWhile):
                lines.append(f"{prefix}WHILE {format_expr(item.condition)}:"); body(item.body, prefix + "  ")
    body(ir.globals, indent)
    for function in ir.functions:
        lines.append(f"{indent}FUNCTION {function.name}({', '.join(function.params)}):")
        body(function.body, indent + "  ")
    return "\n".join(lines)