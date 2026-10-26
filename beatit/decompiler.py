"""Reverse-engineer a native Beat It executable back into .bi source.

The decompiler does NOT read embedded source (there is none). It disassembles the
Windows executable with objdump and "lifts" the machine code back to Beat It, using
the fact that our own code generator (native_codegen.py) emits a small, regular set
of instruction patterns and leaves named symbols in the executable:

    main            program entry (the top-level statements)
    fn_<name>       a user function
    var_<name>      a variable / function parameter (global storage)
    list_<name>     a list literal
    sound_<n>       a sound path string,  str_<n> a string literal
    for_/while_ ... structured loop labels

Each function is lifted by symbolically executing its instructions: registers hold
expression trees instead of numbers, and statements are emitted where the generator
would have stored a variable, called the runtime, or looped.

What can NOT be recovered (information that was never in the executable):
  * import aliases (they are guessed from the folder names),
  * comments, spacing and the original order of functions relative to statements,
  * `double` vs `int` (functions come back as `int`/`void`),
  * decimals such as 0.5, which the native backend already truncated to 0,
  * time units: sleeps/windows come back in the largest whole unit that fits.

Programs the lifter cannot fully understand are still written out, with a
`// unrecognized instruction` comment where it gave up, never a crash.
"""
from __future__ import annotations

import re
import shutil
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path

from errors import BeatItError


# ----------------------------------------------------------------------------
# tool discovery
# ----------------------------------------------------------------------------
def find_objdump() -> str | None:
    """Find objdump on PATH or in standard MinGW installation directories."""
    for name in ("objdump", "x86_64-w64-mingw32-objdump"):
        path = shutil.which(name)
        if path:
            return path
    candidates = [
        r"C:\Program Files\CodeBlocks\MinGW\bin\objdump.exe",
        r"C:\MinGW\bin\objdump.exe",
        r"C:\msys64\mingw64\bin\objdump.exe",
        r"C:\msys64\ucrt64\bin\objdump.exe",
        r"C:\TDM-GCC-64\bin\objdump.exe",
    ]
    for c in candidates:
        if Path(c).is_file():
            return c
    return None


# ----------------------------------------------------------------------------
# PE file access (to read the sound-path / string data the code points at)
# ----------------------------------------------------------------------------
class PEImage:
    """Just enough of the PE format to read a C string at a virtual address."""

    def __init__(self, data: bytes):
        self.data = data
        self.image_base = 0
        self.sections: list[tuple[int, int, int, int]] = []   # (rva, vsize, raw_ptr, raw_size)
        try:
            pe = struct.unpack_from("<I", data, 0x3C)[0]
            if data[pe:pe + 4] != b"PE\0\0":
                return
            n_sections = struct.unpack_from("<H", data, pe + 6)[0]
            opt_size = struct.unpack_from("<H", data, pe + 20)[0]
            opt = pe + 24
            magic = struct.unpack_from("<H", data, opt)[0]
            self.image_base = (struct.unpack_from("<Q", data, opt + 24)[0] if magic == 0x20B
                               else struct.unpack_from("<I", data, opt + 28)[0])
            table = opt + opt_size
            for i in range(n_sections):
                off = table + 40 * i
                vsize, rva, raw_size, raw_ptr = struct.unpack_from("<IIII", data, off + 8)
                self.sections.append((rva, vsize, raw_ptr, raw_size))
        except struct.error:
            self.sections = []

    def cstring(self, va: int) -> str | None:
        rva = va - self.image_base
        for s_rva, vsize, raw_ptr, raw_size in self.sections:
            if s_rva <= rva < s_rva + max(vsize, raw_size):
                start = raw_ptr + (rva - s_rva)
                end = self.data.find(b"\0", start)
                if end == -1:
                    return None
                return self.data[start:end].decode("utf-8", errors="replace")
        return None

    def wav_strings(self) -> list[str]:
        """All *.wav path strings in the file, in file order (used by the fallback)."""
        found, seen = [], set()
        for m in re.finditer(rb"([A-Za-z0-9_./\\-]+\.wav)", self.data):
            s = m.group(1).decode("utf-8", errors="ignore").replace("\\", "/")
            if s not in seen:
                seen.add(s)
                found.append(s)
        return found


# ----------------------------------------------------------------------------
# objdump parsing
# ----------------------------------------------------------------------------
@dataclass
class Ins:
    addr: int
    op: str
    ops: list[str]
    sym: str | None      # symbol name from the "# addr <sym>" annotation or a branch target
    symaddr: int | None
    text: str


_HEADER = re.compile(r"^([0-9a-fA-F]+)\s+<([^>]+)>:\s*$")
_LABEL_NAME = re.compile(r"^(?:for|endfor|while|endwhile)_(\d+)$")


def parse_disassembly(text: str):
    """Split objdump output into segments: name -> list of items.

    An item is ("label", name) or ("ins", Ins). Segments are the user functions
    (fn_*) and main; structured loop labels stay inside the segment they belong to.
    """
    segments: dict[str, list] = {}
    current: list | None = None
    for line in text.splitlines():
        h = _HEADER.match(line.strip())
        if h:
            name = h.group(2)
            if name == "main" or name.startswith("fn_"):
                current = segments.setdefault(name, [])
            elif _LABEL_NAME.match(name) and current is not None:
                current.append(("label", name))
            else:
                current = None
            continue
        if current is None:
            continue
        parts = line.split("\t")
        if len(parts) < 3 or not re.match(r"^\s*[0-9a-fA-F]+:\s*$", parts[0]):
            continue
        body = parts[2].strip()
        comment = None
        if "#" in body:
            body, comment = body.split("#", 1)
            body = body.strip()
        mnemonic, _, rest = body.partition(" ")
        ops = [o.strip() for o in rest.split(",")] if rest.strip() else []
        sym = symaddr = None
        target = comment if comment is not None else rest
        m = re.search(r"([0-9a-fA-F]+)?\s*<([^>+]+)(?:\+0x[0-9a-fA-F]+)?>", target or "")
        if m:
            sym = m.group(2)
            if m.group(1):
                symaddr = int(m.group(1), 16)
        current.append(("ins", Ins(int(parts[0].strip().rstrip(":"), 16), mnemonic, ops, sym, symaddr, body)))
    return segments


# ----------------------------------------------------------------------------
# expressions
# ----------------------------------------------------------------------------
# Expressions are tuples:
#   ("num", int) ("var", name) ("snd", path) ("str", text) ("neg", e)
#   ("bin", op, l, r) ("idx", list, e) ("call", name, [args])
#   ("zero",)  value left by `xor eax, eax`        ("ctr",) / ("item", list)  loop internals
_PREC = {"<": 1, ">": 1, "<=": 1, ">=": 1, "==": 1, "!=": 1, "+": 2, "-": 2, "*": 3, "/": 3}


def num(v: int):
    return ("num", v)


def is_num(e, value=None) -> bool:
    return e[0] == "num" and (value is None or e[1] == value)


def mul(a, b):
    """Multiply, folding the unit factors the generator inserts (x * 1, 2 * 1000)."""
    if is_num(a) and is_num(b):
        return num(a[1] * b[1])
    if is_num(b, 1):
        return a
    if is_num(a, 1):
        return b
    return ("bin", "*", a, b)


class Renderer:
    def __init__(self, aliases: dict[str, str]):
        self.aliases = aliases          # folder path "sounds/piano_notes" -> alias "p"

    def sound(self, path: str) -> str:
        folder, _, file = path.rpartition("/")
        stem = file.rsplit(".", 1)[0]
        alias = self.aliases.get(folder)
        return f"{alias}.{stem}" if alias else stem

    def fmt(self, e, parent: int = 0) -> str:
        kind = e[0]
        if kind == "num":
            return str(e[1]) if e[1] >= 0 or parent == 0 else f"(0 - {-e[1]})"
        if kind == "zero":
            return "0"
        if kind == "var":
            return e[1]
        if kind == "snd":
            return self.sound(e[1])
        if kind == "str":
            return '"' + e[1].replace('"', "'") + '"'
        if kind == "neg":
            return "-" + self.fmt(e[1], 4)
        if kind == "idx":
            return f"{e[1]}[{self.fmt(e[2])}]"
        if kind == "call":
            return f"{e[1]}({', '.join(self.fmt(a) for a in e[2])})"
        if kind == "bin":
            prec = _PREC[e[1]]
            text = f"{self.fmt(e[2], prec)} {e[1]} {self.fmt(e[3], prec + 1)}"
            return f"({text})" if prec < parent else text
        return "0"      # loop internals never reach rendered output


# ----------------------------------------------------------------------------
# the lifter: symbolic execution of one function / main
# ----------------------------------------------------------------------------
_REG64 = {"eax": "rax", "ecx": "rcx", "edx": "rdx", "ebx": "rbx", "al": "rax",
          "r8d": "r8", "r9d": "r9", "r10d": "r10"}
_ARG_REGS = ("rcx", "rdx", "r8", "r9")
_REGS = {"rax", "rcx", "rdx", "rbx", "r8", "r9", "r10", "r11", "rsp", "rbp", "rsi", "rdi"}
_IGNORED = {"nop", "int3", "ud2", "cqo", "cdq", "leave", "data16", "cs", "xchg_ax"}
_SET_OPS = {"setl": "<", "setg": ">", "setle": "<=", "setge": ">=", "sete": "==", "setne": "!="}


def reg(name: str) -> str:
    return _REG64.get(name, name)


def imm(text: str) -> int | None:
    """Parse an immediate operand. Values are 64-bit two's complement, so
    0xfffffffffffffffb is -5 (that is how `mov rax, -5` is disassembled)."""
    try:
        value = int(text, 16) if text.lower().lstrip("-").startswith("0x") else int(text)
    except ValueError:
        return None
    if value >= 1 << 63:
        value -= 1 << 64
    elif 1 << 31 <= value < 1 << 32 and text.lower().startswith("0xffffffff"):
        value -= 1 << 32                  # sign-extended 32-bit immediate
    return value


class Frame:
    def __init__(self, kind: str, label: str):
        self.kind, self.label = kind, label
        self.lines: list[str] = []
        self.cond = None            # while: condition expression
        self.var = None             # for: loop variable
        self.iterable = None        # for: list name or ("range", expr)
        self.header = kind == "for"


class Lifter:
    def __init__(self, items, params_of: dict[str, list[str]], render: Renderer,
                 pe: PEImage, seg_name: str):
        self.items, self.params_of, self.r, self.pe = items, params_of, render, pe
        self.seg = seg_name
        self.regs: dict[str, tuple] = {}
        self.stack: list[tuple] = []
        self.frames = [Frame("top", "")]
        self.pending_call = None            # call result in rax nobody has used yet
        self.list_pending: tuple[str, list] | None = None
        self.r8_list: str | None = None
        self.cmp: tuple | None = None
        self.cond = ("num", 1)              # value tested by the last `test rax, rax`
        self.limit_expr = None              # count stored by the last `loop_limit_N` spill
        self.has_value_return = False
        self.in_prologue = seg_name != "main"
        self.problems: list[str] = []
        self.last_ret = max((i for i, (k, v) in enumerate(items) if k == "ins" and v.op == "ret"), default=-1)

    # -- registers --------------------------------------------------------
    def get(self, name: str):
        name = reg(name)
        if name == "rax":
            self.pending_call = None           # someone consumed the call result
        return self.regs.get(name, ("var", f"<{name}>"))

    def set(self, name: str, value):
        name = reg(name)
        if name == "rax":
            self.flush_call()
        self.regs[name] = value

    def operand_value(self, text: str):
        text = text.strip()
        if text.startswith("QWORD PTR") or text.startswith("DWORD PTR"):
            return None
        v = imm(text)
        if v is not None:
            return num(v)
        return self.get(text)

    # -- output -----------------------------------------------------------
    @property
    def top(self) -> Frame:
        return self.frames[-1]

    def emit(self, text: str):
        self.flush_list()
        self.top.lines.append(text)

    def flush_call(self):
        if self.pending_call is not None:
            call, self.pending_call = self.pending_call, None
            self.emit(self.r.fmt(call))

    def flush_list(self):
        if self.list_pending is not None:
            name, items = self.list_pending
            self.list_pending = None
            self.top.lines.append(f"{name} = [{', '.join(self.r.fmt(i) for i in items)}]")

    def assign(self, name: str, value):
        if value[0] == "bin" and value[1] == "+" and value[3] == ("var", name):
            self.emit(f"{name} += {self.r.fmt(value[2])}")       # generated from `x += a`
        else:
            self.emit(f"{name} = {self.r.fmt(value)}")

    def unknown(self, ins: Ins):
        note = f"// unrecognized instruction: {ins.text}"
        self.problems.append(note)
        self.emit(note)

    # -- the instruction handlers ------------------------------------------
    def run(self):
        for index, (kind, item) in enumerate(self.items):
            if kind == "label":
                self.label(item)
            else:
                self.instruction(item, index)
        self.flush_call()
        self.flush_list()
        return self.frames[0].lines

    def label(self, name: str):
        self.flush_call()
        self.flush_list()
        if name.startswith("for_"):
            self.frames.append(Frame("for", name))
        elif name.startswith("while_"):
            self.frames.append(Frame("while", name))
        elif name.startswith("endfor_") or name.startswith("endwhile_"):
            if len(self.frames) > 1:
                frame = self.frames.pop()
                header = self.loop_header(frame)
                self.top.lines.append(header)
                body = frame.lines or ["// (empty loop body)"]
                self.top.lines.extend("    " + line for line in body)

    def loop_header(self, frame: Frame) -> str:
        if frame.kind == "while":
            return f"while {self.r.fmt(frame.cond) if frame.cond else '1'}:"
        var = frame.var or "i"
        it = frame.iterable
        if isinstance(it, str):
            return f"for {var} in {it}:"
        if it is not None and it[0] == "range":
            return f"for {var} in range({self.r.fmt(it[1])}):"
        return f"for {var} in range(0):"

    def instruction(self, ins: Ins, index: int):
        op, ops = ins.op, ins.ops
        if op in _IGNORED or (op == "xchg" and ops and ops[0] == "ax"):
            return
        if self.in_prologue:
            if op in ("push", "sub") or (op == "mov" and ops and ops[0] == "rbp"):
                return
            if op == "mov" and len(ops) == 2 and ops[1] in _ARG_REGS and ins.sym and ins.sym.startswith("var_"):
                return      # parameter spill: names were collected up front
            self.in_prologue = False

        if op in ("mov", "movabs"):
            self.mov(ins)
        elif op == "lea":
            self.lea(ins)
        elif op == "push":
            if ops[0] != "rbp":
                self.stack.append(self.get(ops[0]))
        elif op == "pop":
            if ops[0] != "rbp":
                self.set(ops[0], self.stack.pop() if self.stack else ("var", "<empty>"))
        elif op == "xor" and len(ops) == 2 and reg(ops[0]) == reg(ops[1]):
            self.set(ops[0], ("zero",))
        elif op in ("add", "sub", "imul"):
            self.arith(ins)
        elif op == "neg":
            self.set(ops[0], ("neg", self.get(ops[0])))
        elif op == "idiv":
            self.set("rax", ("bin", "/", self.get("rax"), self.get(ops[0])))
        elif op == "xchg" and len(ops) == 2:
            a, b = self.get(ops[0]), self.get(ops[1])
            self.set(ops[0], b)
            self.set(ops[1], a)
        elif op == "cmp":
            self.compare(ins)
        elif op in _SET_OPS:
            left, right = self.cmp if self.cmp else (("var", "?"), ("var", "?"))
            self.set("rax", ("bin", _SET_OPS[op], left, right))
        elif op == "movzx":
            pass
        elif op == "test":
            self.cond = self.get(ops[0])
        elif op in ("jz", "je"):
            if self.top.kind == "while" and self.top.cond is None:
                self.top.cond = self.cond
        elif op in ("jmp", "jge", "jl", "jg", "jle", "jne", "inc", "dec"):
            self.flush_call()
        elif op == "call":
            self.call(ins)
        elif op != "ret":
            self.unknown(ins)
        if op == "ret":
            self.ret(index)

    def ret(self, index: int):
        value = self.get("rax")
        self.flush_list()
        if index == self.last_ret:
            return                       # the generated function epilogue
        if value[0] == "zero":
            self.emit("return")
        else:
            self.has_value_return = True
            self.emit(f"return {self.r.fmt(value)}")

    def mov(self, ins: Ins):
        dst, src = ins.ops
        if dst.startswith("QWORD PTR") or dst.startswith("DWORD PTR"):
            self.store(ins, dst, src)
            return
        if src.startswith("QWORD PTR") or src.startswith("DWORD PTR"):
            self.load(ins, dst, src)
            return
        v = imm(src)
        self.set(dst, num(v) if v is not None else self.get(src))

    def load(self, ins: Ins, dst: str, src: str):
        sym = ins.sym or ""
        if sym.startswith("var_"):
            self.set(dst, ("var", sym[4:]))
        elif sym.startswith("loop_idx_"):
            self.set(dst, ("ctr",))
        elif "r8+rax*8" in src.replace(" ", ""):
            self.set(dst, ("idx", self.r8_list or "?", self.get("rax")))
        elif "r8+rdx*8" in src.replace(" ", ""):
            if self.top.kind == "for":
                self.top.iterable = self.r8_list
            self.set(dst, ("item", self.r8_list))
        else:
            self.unknown(ins)

    def store(self, ins: Ins, dst: str, src: str):
        sym = ins.sym or ""
        value = num(imm(src)) if imm(src) is not None else None
        if value is None:
            value = self.get(src)
        if sym.startswith("var_"):
            name = sym[4:]
            if self.top.kind == "for" and self.top.header:
                self.top.var, self.top.header = name, False
                if self.top.iterable is None and self.limit_expr is not None:
                    self.top.iterable = ("range", self.limit_expr)
            else:
                self.assign(name, value)
        elif sym.startswith("loop_limit_"):
            self.limit_expr = value
        elif sym.startswith("loop_idx_"):
            pass
        elif dst.replace(" ", "").startswith("QWORDPTR[r8"):
            m = re.search(r"r8\+(0x[0-9a-fA-F]+|\d+)", dst)
            slot = (imm(m.group(1)) // 8) if m else 0
            name = self.r8_list or "?"
            if self.list_pending is None or self.list_pending[0] != name or slot == 0:
                self.flush_list()
                self.list_pending = (name, [])
            self.list_pending[1].append(value)
        else:
            self.unknown(ins)

    def lea(self, ins: Ins):
        dst = ins.ops[0]
        sym = ins.sym or ""
        if sym.startswith("sound_") and ins.symaddr is not None:
            path = self.pe.cstring(ins.symaddr) or sym
            self.set(dst, ("snd", path))
        elif sym.startswith("str_") and ins.symaddr is not None:
            self.set(dst, ("str", self.pe.cstring(ins.symaddr) or ""))
        elif sym.startswith("list_"):
            self.r8_list = sym[5:]
            if reg(dst) != "r8":
                self.set(dst, ("var", sym[5:]))
        else:
            self.unknown(ins)

    def arith(self, ins: Ins):
        op, ops = ins.op, ins.ops
        dst = ops[0]
        if op == "imul" and len(ops) == 3:                 # imul rax, rax, 0x3e8
            a, b = self.get(ops[1]), num(imm(ops[2]) or 0)
            self.set(dst, mul(a, b))
            return
        a = self.get(dst)
        b = num(imm(ops[1])) if imm(ops[1]) is not None else self.get(ops[1])
        if dst in ("rsp", "rbp"):
            return
        if op == "imul":
            self.set(dst, mul(a, b))
        else:
            self.set(dst, ("bin", "+" if op == "add" else "-", a, b))

    def compare(self, ins: Ins):
        a, b = ins.ops
        sym = ins.sym or ""
        if self.top.kind == "for" and self.top.header and (sym.startswith("loop_limit_") or imm(b) is not None):
            return                      # the loop-exit test of a for header; the bound is already known
        left = self.get(a)
        right = num(imm(b)) if imm(b) is not None else self.get(b)
        self.cmp = (left, right)

    def call(self, ins: Ins):
        target = ins.sym or ""
        self.flush_call()
        if target == "beatit_play":
            beat, start, end, flag = (self.get(r) for r in ("rcx", "rdx", "r8", "r9"))
            self.flush_list()
            self.emit(self.play_text(beat, start, end, flag))
        elif target == "beatit_sleep":
            self.emit(self.sleep_text(self.get("rcx")))
        elif target == "beatit_set_volume":
            self.emit(f"volume = {self.r.fmt(self.get('rcx'))}")
        elif target.startswith("fn_"):
            name = target[3:]
            count = len(self.params_of.get(name, []))
            args = [self.get(r) for r in _ARG_REGS[:count]]
            call = ("call", name, args)
            self.regs["rax"] = call
            self.pending_call = call
        else:
            self.unknown(ins)

    # -- statement text -----------------------------------------------------
    def play_text(self, beat, start, end, flag) -> str:
        name = "play_async" if is_num(flag, 1) else "play"
        b = self.r.fmt(beat)
        if is_num(start, 0) and is_num(end, 0):
            return f"{name}({b})"
        if is_num(end, 0):
            return f"{name}({b}, {self.r.fmt(start)})"
        if is_num(start) and is_num(end) and start[1] % 1000 == 0 and end[1] % 1000 == 0:
            return f"{name}({b}, {start[1] // 1000}, {end[1] // 1000}, s)"
        return f"{name}({b}, {self.r.fmt(start)}, {self.r.fmt(end)}, ms)"

    def sleep_text(self, amount) -> str:
        if is_num(amount):
            ms = amount[1]
            if ms != 0 and ms % 1000 == 0:
                return f"sleep({ms // 1000}, s)"
            return f"sleep({ms}, ms)"
        if amount[0] == "bin" and amount[1] == "*" and is_num(amount[3]):
            unit = {1000: "s", 60000: "min", 3600000: "hr"}.get(amount[3][1])
            if unit:
                return f"sleep({self.r.fmt(amount[2])}, {unit})"
        return f"sleep({self.r.fmt(amount)}, ms)"


def collect_params(items) -> list[str]:
    """Parameter names = the spills of rcx/rdx/r8/r9 into var_<name> at function entry."""
    names: dict[int, str] = {}
    for kind, item in items:
        if kind != "ins":
            continue
        if item.op in ("push", "sub") or (item.op == "mov" and item.ops and item.ops[0] == "rbp"):
            continue
        if item.op == "mov" and len(item.ops) == 2 and item.ops[1] in _ARG_REGS \
                and item.sym and item.sym.startswith("var_"):
            names[_ARG_REGS.index(item.ops[1])] = item.sym[4:]
            continue
        break
    return [names[i] for i in sorted(names)]


# ----------------------------------------------------------------------------
# imports (aliases are not stored in the executable, so they are chosen here)
# ----------------------------------------------------------------------------
def choose_aliases(paths: list[str]) -> dict[str, str]:
    """Map each sound folder ("sounds/noise") to a short alias, avoiding clashes."""
    folders = []
    for p in paths:
        folder = p.rpartition("/")[0] or "sounds"
        if folder not in folders:
            folders.append(folder)
    aliases: dict[str, str] = {}
    taken: set[str] = set()
    for folder in sorted(folders, key=lambda f: (f.count("/"), f)):
        leaf = folder.rsplit("/", 1)[-1]
        alias = leaf[0] if leaf else "s"
        size = 1
        while alias in taken or alias in ("s", "ms", "min", "hr") and alias != "s":
            size += 1
            alias = leaf[:size] if size <= len(leaf) else f"{leaf[0]}{size}"
        taken.add(alias)
        aliases[folder] = alias
    return aliases


# ----------------------------------------------------------------------------
# driver
# ----------------------------------------------------------------------------
HEADER = [
    "// =================================================================",
    "// Decompiled from native Windows executable: {name}",
    "// Reverse-engineered from machine code & data sections",
    "// =================================================================",
]


def run_objdump(objdump: str, executable: Path) -> str:
    try:
        return subprocess.run([objdump, "-d", "-M", "intel", str(executable)],
                              capture_output=True, text=True, check=True).stdout
    except Exception:
        return ""


def decompile_file(executable_file: str | Path, output_file: str | Path | None = None) -> Path:
    """Disassemble a native Beat It .exe and rebuild a .bi source file from it."""
    executable = Path(executable_file).resolve()
    if not executable.is_file():
        raise FileNotFoundError(executable)
    if executable.suffix.lower() != ".exe":
        raise BeatItError("Decompiler input must be a native Windows .exe file")
    data = executable.read_bytes()
    if not data.startswith(b"MZ"):
        raise BeatItError("File is not a valid Windows PE executable")

    pe = PEImage(data)
    objdump = find_objdump()
    segments = parse_disassembly(run_objdump(objdump, executable)) if objdump else {}

    lines = [h.format(name=executable.name) for h in HEADER] + [""]
    if "main" in segments:
        lines += lift_program(segments, pe)
    else:
        lines += fallback_program(pe, bool(objdump))

    output = Path(output_file) if output_file else executable.with_suffix(".bi")
    output = output.resolve().with_suffix(".bi")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output


def lift_program(segments: dict, pe: PEImage) -> list[str]:
    # sound paths first, so imports and aliases are known before any expression is printed
    sound_paths: list[str] = []
    for items in segments.values():
        for kind, ins in items:
            if kind == "ins" and ins.op == "lea" and ins.sym and ins.sym.startswith("sound_") \
                    and ins.symaddr is not None:
                path = pe.cstring(ins.symaddr)
                if path and path not in sound_paths:
                    sound_paths.append(path)
    aliases = choose_aliases(sound_paths)
    renderer = Renderer(aliases)

    params_of = {name[3:]: collect_params(items) for name, items in segments.items() if name.startswith("fn_")}

    out: list[str] = []
    for folder, alias in aliases.items():
        out.append(f"import from {folder.replace('/', '.')} as {alias}")
    if aliases:
        out.append("")

    for name, items in segments.items():
        if not name.startswith("fn_"):
            continue
        fname = name[3:]
        lifter = Lifter(items, params_of, renderer, pe, name)
        body = lifter.run()
        kind = "int" if lifter.has_value_return else "void"
        out.append(f"{kind} {fname}({', '.join(params_of[fname])}):")
        out.extend("    " + line for line in (body or ["// (empty function)"]))
        out.append("")

    main = Lifter(segments["main"], params_of, renderer, pe, "main")
    out.extend(main.run())
    return out


def fallback_program(pe: PEImage, had_objdump: bool) -> list[str]:
    """No usable disassembly (objdump missing, or the executable was stripped of symbols)."""
    why = "objdump not found" if not had_objdump else "no Beat It symbols found (stripped executable?)"
    paths = pe.wav_strings()
    aliases = choose_aliases(paths)
    renderer = Renderer(aliases)
    out = [f"// Note: {why}; reconstructed from the sound paths only"]
    for folder, alias in aliases.items():
        out.append(f"import from {folder.replace('/', '.')} as {alias}")
    out.append("")
    names = []
    for idx, path in enumerate(paths, start=1):
        names.append(f"beat{idx}")
        out.append(f"beat{idx} = {renderer.sound(path)}")
    if names:
        out += ["", f"order = [{', '.join(names)}]", "", "for i in order:", "    play(i)"]
    return out
