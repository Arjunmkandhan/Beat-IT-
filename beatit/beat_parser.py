"""PHASE 2 - Syntax analysis (recursive-descent parser). Builds the AST.""" 
"""Using LL(1) parsing - recursive descent and selective cases it uses LL(2) """

from ast_nodes import *
from errors import BeatItError

UNITS = {"s", "ms", "min", "hr"}
TYPES = {"int", "double", "string", "void"}
COMPARE_OPS = {"<", ">", "<=", ">=", "==", "!="}


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self, offset=0):
        return self.tokens[min(self.pos + offset, len(self.tokens) - 1)]

    def advance(self):
        tok = self.tokens[self.pos]
        if tok.kind != "EOF":
            self.pos += 1
        return tok

    def at(self, kind, value=None, offset=0):
        tok = self.peek(offset) # offset -> look ahead 
        return tok.kind == kind and (value is None or tok.value == value)

    def accept(self, kind, value=None):
        return self.advance() if self.at(kind, value) else None

    def expect(self, kind, value=None):
        if self.at(kind, value):
            return self.advance()
        tok = self.peek()
        wanted = value if value else kind.lower()
        raise BeatItError(f"Expected {wanted!r} but found {self.describe(tok)}", tok.line)

    @staticmethod
    def describe(tok):
        return {"NEWLINE": "end of line", "EOF": "end of file",
                "INDENT": "an unexpected indent", "DEDENT": "end of block"}.get(tok.kind, repr(tok.value))

    def end_of_line(self):
        self.expect("NEWLINE")

    # @dataclass
    # class Program:
    #     body: List[Any]
    def parse_program(self):
        body = []
        while not self.at("EOF"):
            body.append(self.statement(top=True))
        return Program(body)

    def block(self):
        self.expect("OP", ":")
        self.expect("NEWLINE")
        if not self.at("INDENT"):
            raise BeatItError("Expected an indented block", self.peek().line)
        self.advance()
        body = []
        while not self.at("DEDENT") and not self.at("EOF"):
            body.append(self.statement())
        self.expect("DEDENT")
        return body

    def statement(self, top=False):
        tok = self.peek()
        if tok.kind == "KEYWORD":
            v = tok.value
            if v == "import":
                if not top:
                    raise BeatItError("'import' is only allowed at the top level", tok.line)
                return self.import_stmt()
            if v in TYPES:
                if not top:
                    raise BeatItError("Functions can only be defined at the top level", tok.line)
                return self.func_def()
            if v == "volume":       return self.volume_stmt()
            if v in ("play", "play_async"): return self.play_stmt(is_async=(v == "play_async"))
            if v == "sleep":        return self.sleep_stmt()
            if v == "for":          return self.for_stmt()
            if v == "while":        return self.while_stmt()
            if v == "return":       return self.return_stmt()
        elif tok.kind == "IDENT":
            nxt = self.peek(1)
            if nxt.kind == "OP" and nxt.value in ("=", "+="):
                return self.assignment()
            if nxt.kind == "OP" and nxt.value == "(":
                stmt = CallStmt(self.call_expr(), tok.line)
                self.end_of_line()
                return stmt
            raise BeatItError(f"Unexpected {self.describe(nxt)} after {tok.value!r}", tok.line)
        raise BeatItError(f"Unexpected {self.describe(tok)}", tok.line)

    def import_stmt(self):
        line = self.advance().line
        self.expect("KEYWORD", "from")
        items = []
        while True:
            path = [self.expect("IDENT").value]
            while self.accept("OP", "."):
                path.append(self.expect("IDENT").value)
            alias = self.expect("IDENT").value if self.accept("KEYWORD", "as") else None
            items.append((path, alias))
            if not self.accept("OP", ","):
                break
        self.end_of_line()
        return Import(items, line)

    def volume_stmt(self):
        line = self.advance().line
        self.expect("OP", "=")
        value = self.expr()
        self.end_of_line()
        return Volume(value, line)

    def assignment(self):
        name = self.advance()
        op = self.advance().value
        value = self.expr()
        self.end_of_line()
        if op == "=":
            return Assign(name.value, value, name.line)
        return AugAssign(name.value, "+", value, name.line)

    def unit(self):
        tok = self.expect("IDENT")
        if tok.value not in UNITS:
            raise BeatItError(f"Unknown time unit {tok.value!r} (use s, ms, min or hr)", tok.line)
        return tok.value

    def play_stmt(self, is_async=False):
        line = self.advance().line
        self.expect("OP", "(")
        beat = self.expr()
        start = end = unit = None
        if self.accept("OP", ","):
            start = self.expr()
            if self.accept("OP", ","):
                end = self.expr()
                if self.accept("OP", ","):
                    unit = self.unit()
        self.expect("OP", ")")
        self.end_of_line()
        return Play(beat, start, end, unit, is_async, line)

    def sleep_stmt(self):
        line = self.advance().line
        self.expect("OP", "(")
        amount = self.expr()
        unit = self.unit() if self.accept("OP", ",") else None
        self.expect("OP", ")")
        self.end_of_line()
        return Sleep(amount, unit, line)

    def for_stmt(self):
        line = self.advance().line
        var = self.expect("IDENT").value
        self.expect("KEYWORD", "in")
        if self.at("KEYWORD", "range"):
            rline = self.advance().line
            self.expect("OP", "(")
            count = self.expr()
            self.expect("OP", ")")
            iterable = Range(count, rline)
        else:
            iterable = self.expr()
        return For(var, iterable, self.block(), line)

    def while_stmt(self):
        line = self.advance().line
        cond = self.expr()
        return While(cond, self.block(), line)

    def func_def(self):
        ret = self.advance()
        name = self.expect("IDENT").value
        self.expect("OP", "(")
        params = []
        if not self.at("OP", ")"):
            params.append(self.expect("IDENT").value)
            while self.accept("OP", ","):
                params.append(self.expect("IDENT").value)
        self.expect("OP", ")")
        return FuncDef(ret.value, name, params, self.block(), ret.line)

    def return_stmt(self):
        line = self.advance().line
        value = None if self.at("NEWLINE") else self.expr()
        self.end_of_line()
        return Return(value, line)

    def expr(self): # handles the comparison == , < 
        left = self.additive()
        tok = self.peek()
        if tok.kind == "OP" and tok.value in COMPARE_OPS:
            self.advance()
            left = BinOp(tok.value, left, self.additive(), tok.line)
        return left

    def additive(self): 
        left = self.term()
        while self.peek().kind == "OP" and self.peek().value in ("+", "-"):
            op = self.advance()
            left = BinOp(op.value, left, self.term(), op.line)
        return left

    def term(self):
        left = self.unary()
        while self.peek().kind == "OP" and self.peek().value in ("*", "/"):
            op = self.advance()
            left = BinOp(op.value, left, self.unary(), op.line)
        return left

    def unary(self):
        if self.at("OP", "-"):
            tok = self.advance()
            return UnaryMinus(self.unary(), tok.line)
        return self.postfix()

    def postfix(self):
        node = self.primary()
        while self.at("OP", "["):
            line = self.advance().line
            index = self.expr()
            self.expect("OP", "]")
            node = Index(node, index, line)
        return node

    def call_expr(self):
        name = self.expect("IDENT")
        self.expect("OP", "(")
        args = []
        if not self.at("OP", ")"):
            args.append(self.expr())
            while self.accept("OP", ","):
                args.append(self.expr())
        self.expect("OP", ")")
        return Call(name.value, args, name.line)

    def primary(self):
        tok = self.peek()
        if tok.kind in ("INT", "DOUBLE"):
            self.advance()
            return Num(tok.value, tok.line)
        if tok.kind == "STRING":
            self.advance()
            return Str(tok.value, tok.line)
        if self.at("OP", "("):
            self.advance()
            e = self.expr()
            self.expect("OP", ")")
            return e
        if self.at("OP", "["):
            self.advance()
            items = []
            if not self.at("OP", "]"):
                items.append(self.expr())
                while self.accept("OP", ","):
                    items.append(self.expr())
            self.expect("OP", "]")
            return ListLit(items, tok.line)
        if tok.kind == "IDENT":
            if self.at("OP", "(", offset=1):
                return self.call_expr()
            self.advance()
            parts = [tok.value]
            while self.accept("OP", "."):
                parts.append(self.expect("IDENT").value)
            if len(parts) == 1:
                return Var(tok.value, tok.line)
            return Qualified(".".join(parts[:-1]), parts[-1], tok.line)
        raise BeatItError(f"Unexpected {self.describe(tok)} in expression", tok.line)