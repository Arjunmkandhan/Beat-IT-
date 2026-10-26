"""PHASE 3 - Semantic analysis. Runs BEFORE the program starts, so mistakes are
reported without playing half a song.

Checks: imports exist, sounds exist, functions are defined (anywhere in the file)
and called with the right argument count, variables are known, 'return' rules,
'volume' only at top level."""
from pathlib import Path
from ast_nodes import *
from assets import find_sound_file, SOUND_EXTENSIONS
from errors import BeatItError


class SemanticAnalyzer:
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.modules = {}      # alias (or dotted path) -> folder
        self.functions = {}    # name -> FuncDef

    def analyze(self, program): # program is the AST 
        # pass 1: collect imports and function signatures (so order does not matter)
        for stmt in program.body:
            if isinstance(stmt, Import):
                self.register_import(stmt)
            elif isinstance(stmt, FuncDef):
                if stmt.name in self.functions:
                    raise BeatItError(f"Function {stmt.name!r} is already defined "
                                      f"(line {self.functions[stmt.name].line})", stmt.line)
                self.functions[stmt.name] = stmt
        # pass 2: check every statement
        global_names = self.assigned_names(program.body)
        for stmt in program.body:
            self.check_stmt(stmt, global_names, None, 0)

    def register_import(self, stmt):
        for path, alias in stmt.items:
            folder = self.base_dir.joinpath(*path)
            if not folder.is_dir():
                raise BeatItError(f"Sound folder '{'/'.join(path)}' not found next to the code file", stmt.line)
            key = alias or ".".join(path)
            if key in self.modules:
                raise BeatItError(f"Name {key!r} is imported twice", stmt.line)
            self.modules[key] = folder

    def assigned_names(self, stmts):
        names = set()
        for s in stmts:
            if isinstance(s, Assign):
                names.add(s.name)
            elif isinstance(s, For):
                names.add(s.var)
                names |= self.assigned_names(s.body)
            elif isinstance(s, While):
                names |= self.assigned_names(s.body)
        return names

    # ---------- statements ----------
    def check_stmt(self, s, names, func, depth):
        if isinstance(s, (Import,)):
            return
        if isinstance(s, FuncDef):
            local = set(s.params) | self.assigned_names(s.body) | names
            for st in s.body:
                self.check_stmt(st, local, s, 0)
        elif isinstance(s, Volume):
            if func is not None or depth > 0:
                raise BeatItError("'volume' must be set at the top level of the program", s.line)
            self.check_expr(s.value, names)
        elif isinstance(s, Assign):
            self.check_expr(s.value, names)
        elif isinstance(s, AugAssign):
            self.need_var(s.name, names, s.line)
            self.check_expr(s.value, names)
        elif isinstance(s, Play):
            for e in (s.beat, s.start, s.end):
                if e is not None:
                    self.check_expr(e, names)
        elif isinstance(s, Sleep):
            self.check_expr(s.amount, names)
        elif isinstance(s, For):
            self.check_expr(s.iterable, names)
            for st in s.body:
                self.check_stmt(st, names, func, depth + 1)
        elif isinstance(s, While):
            self.check_expr(s.cond, names)
            for st in s.body:
                self.check_stmt(st, names, func, depth + 1)
        elif isinstance(s, Return):
            if func is None:
                raise BeatItError("'return' outside a function", s.line)
            if func.ret_type == "void" and s.value is not None:
                raise BeatItError(f"void function {func.name!r} cannot return a value", s.line)
            if func.ret_type != "void" and s.value is None:
                raise BeatItError(f"Function {func.name!r} must return a {func.ret_type}", s.line)
            if s.value is not None:
                self.check_expr(s.value, names)
        elif isinstance(s, CallStmt):
            self.check_call(s.call, names)

    # ---------- expressions ----------
    def need_var(self, name, names, line):
        if name not in names:
            raise BeatItError(f"Undefined variable {name!r}", line)

    def check_call(self, c, names):
        fn = self.functions.get(c.name)
        if fn is None:
            raise BeatItError(f"Undefined function {c.name!r}", c.line)
        if len(c.args) != len(fn.params):
            raise BeatItError(f"{c.name}() takes {len(fn.params)} argument(s) but {len(c.args)} given", c.line)
        for a in c.args:
            self.check_expr(a, names)
        return fn

    def check_expr(self, e, names):
        if isinstance(e, Var):
            self.need_var(e.name, names, e.line)
        elif isinstance(e, Qualified):
            folder = self.modules.get(e.module)
            if folder is None:
                raise BeatItError(f"Unknown module {e.module!r} (did you import it?)", e.line)
            if find_sound_file(folder, e.sound) is None:
                raise BeatItError(f"Sound {e.sound!r} not found in '{folder.name}' "
                                  f"(looked for {', '.join(SOUND_EXTENSIONS)})", e.line)
        elif isinstance(e, Call):
            fn = self.check_call(e, names)
            if fn.ret_type == "void":
                raise BeatItError(f"void function {e.name!r} has no value to use", e.line)
        elif isinstance(e, BinOp):
            self.check_expr(e.left, names); self.check_expr(e.right, names)
        elif isinstance(e, UnaryMinus):
            self.check_expr(e.operand, names)
        elif isinstance(e, Index):
            self.check_expr(e.target, names); self.check_expr(e.index, names)
        elif isinstance(e, ListLit):
            for i in e.items:
                self.check_expr(i, names)
        elif isinstance(e, Range):
            self.check_expr(e.count, names)
