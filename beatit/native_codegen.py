"""Phase 6: direct x86-64 Intel-syntax assembly generation for Beat It."""
from ast_nodes import *
from ir import *
from errors import BeatItError


class NativeCodeGenerator:
    """Turns optimized IR into GAS-compatible Windows x86-64 assembly.

    GCC is used only to assemble/link this text and the fixed native runtime.
    No generated Beat It statement is translated through C.
    """
    def __init__(self, sound_paths):
        self.sound_paths = sound_paths
        self.lines = []
        self.data = []
        self.bss = []
        self.labels = {}
        self.variables = set()
        self.lists = {}
        self.number = 0

    def fresh(self, prefix):
        self.number += 1
        return f"{prefix}_{self.number}"

    def sound_label(self, path):
        if path not in self.labels:
            label = f"sound_{len(self.labels)}"
            self.labels[path] = label
            self.data.extend([".section .rdata,\"dr\"", f"{label}: .asciz \"{path}\""])
        return self.labels[path]

    def collect(self, statements):
        for s in statements:
            if isinstance(s, (IRAssign, IRAugAssign)):
                self.variables.add(s.name)
                if isinstance(s, IRAssign) and isinstance(s.value, ListLit):
                    label = f"list_{s.name}"
                    if s.name not in self.lists:
                        self.lists[s.name] = (label, len(s.value.items))
                        self.bss.append(f"{label}: .zero {8 * len(s.value.items)}")
            elif isinstance(s, IRFor):
                self.variables.add(s.variable)
                self.collect(s.body)
            elif isinstance(s, IRWhile):
                self.collect(s.body)

    def generate(self, ir):
        self.collect(ir.globals)
        for fn in ir.functions:
            self.collect(fn.body)
            for p in fn.params:
                self.variables.add(p)

        for name in sorted(self.variables):
            self.bss.append(f"var_{name}: .quad 0")

        self.lines = [
            ".intel_syntax noprefix",
            ".extern beatit_play",
            ".extern beatit_sleep",
            ".extern beatit_set_volume",
            ".text",
        ]

        # Generate user functions first
        for fn in ir.functions:
            self.function_def(fn)

        # Generate main entry point
        self.lines.extend([
            ".globl main",
            "main:",
            "  push rbp",
            "  mov rbp, rsp",
            "  sub rsp, 32"
        ])
        self.block(ir.globals)
        self.lines.extend([
            "  xor eax, eax",
            "  add rsp, 32",
            "  pop rbp",
            "  ret"
        ])

        asm_parts = self.lines + self.data
        if self.bss:
            asm_parts.extend([".bss"] + self.bss)
        return "\n".join(asm_parts) + "\n"

    def function_def(self, fn):
        self.lines.extend([
            f".globl fn_{fn.name}",
            f"fn_{fn.name}:",
            "  push rbp",
            "  mov rbp, rsp",
            "  sub rsp, 32"
        ])
        param_regs = ["rcx", "rdx", "r8", "r9"]
        for idx, param in enumerate(fn.params[:4]):
            self.lines.append(f"  mov QWORD PTR [rip + var_{param}], {param_regs[idx]}")
        self.block(fn.body)
        self.lines.extend([
            "  xor eax, eax",
            "  add rsp, 32",
            "  pop rbp",
            "  ret"
        ])

    def call_expr(self, call):
        param_regs = ["rcx", "rdx", "r8", "r9"]
        for arg in call.args[:4]:
            self.expression(arg)
            self.lines.append("  push rax")
        for idx in range(len(call.args[:4]) - 1, -1, -1):
            self.lines.append(f"  pop {param_regs[idx]}")
        self.lines.append(f"  call fn_{call.name}")

    def expression(self, expr):
        if isinstance(expr, Num):
            self.lines.append(f"  mov rax, {int(expr.value)}")
        elif isinstance(expr, Var):
            self.lines.append(f"  mov rax, QWORD PTR [rip + var_{expr.name}]")
        elif isinstance(expr, Qualified):
            self.lines.append(f"  lea rax, [rip + {self.sound_label(self.sound_paths[(expr.module, expr.sound)])}]")
        elif isinstance(expr, UnaryMinus):
            self.expression(expr.operand)
            self.lines.append("  neg rax")
        elif isinstance(expr, BinOp):
            self.expression(expr.left)
            self.lines.append("  mov r10, rax")
            self.expression(expr.right)
            self.lines.extend(["  xchg rax, r10"])
            arithmetic = {
                "+": ["  add rax, r10"],
                "-": ["  sub rax, r10"],
                "*": ["  imul rax, r10"],
                "/": ["  cqo", "  idiv r10"]
            }
            if expr.op in arithmetic:
                self.lines.extend(arithmetic[expr.op])
            else:
                jumps = {"<": "setl", ">": "setg", "<=": "setle", ">=": "setge", "==": "sete", "!=": "setne"}
                self.lines.extend(["  cmp rax, r10", f"  {jumps[expr.op]} al", "  movzx rax, al"])
        elif isinstance(expr, Index):
            if isinstance(expr.target, Var) and expr.target.name in self.lists:
                label, _ = self.lists[expr.target.name]
                self.expression(expr.index)
                self.lines.extend([
                    f"  lea r8, [rip + {label}]",
                    "  mov rax, QWORD PTR [r8 + rax*8]"
                ])
            else:
                raise BeatItError("Array indexing supported on list variables", getattr(expr, "line", None))
        elif isinstance(expr, Call):
            self.call_expr(expr)
        else:
            raise BeatItError(f"Native backend cannot lower {type(expr).__name__}", getattr(expr, "line", None))

    def block(self, statements):
        for statement in statements:
            if isinstance(statement, IRAssign):
                if isinstance(statement.value, ListLit):
                    label, _ = self.lists[statement.name]
                    for i, value in enumerate(statement.value.items):
                        self.expression(value)
                        self.lines.extend([
                            f"  lea r8, [rip + {label}]",
                            f"  mov QWORD PTR [r8 + {8*i}], rax"
                        ])
                else:
                    self.expression(statement.value)
                    self.lines.append(f"  mov QWORD PTR [rip + var_{statement.name}], rax")
            elif isinstance(statement, IRAugAssign):
                self.lines.append(f"  mov r10, QWORD PTR [rip + var_{statement.name}]")
                self.expression(statement.value)
                if statement.op == "+":
                    self.lines.append("  add rax, r10")
                else:
                    self.lines.extend(["  sub r10, rax", "  mov rax, r10"])
                self.lines.append(f"  mov QWORD PTR [rip + var_{statement.name}], rax")
            elif isinstance(statement, IRPlay):
                unit_factor = {"ms": 1, "s": 1000, "min": 60000, "hr": 3600000}[statement.unit or "ms"]
                
                # 1. Evaluate end time (r8)
                if statement.end is not None:
                    self.expression(statement.end)
                    if unit_factor > 1:
                        self.lines.append(f"  imul rax, {unit_factor}")
                else:
                    self.lines.append("  mov rax, 0")
                self.lines.append("  push rax")

                # 2. Evaluate start time (rdx)
                if statement.start is not None:
                    self.expression(statement.start)
                    if unit_factor > 1:
                        self.lines.append(f"  imul rax, {unit_factor}")
                else:
                    self.lines.append("  mov rax, 0")
                self.lines.append("  push rax")

                # 3. Evaluate beat path (rcx)
                self.expression(statement.beat)
                self.lines.append("  mov rcx, rax")

                # 4. Pop parameters into x64 register calling convention (rcx, rdx, r8, r9)
                self.lines.extend([
                    "  pop rdx",
                    "  pop r8",
                    f"  mov r9, {1 if statement.is_async else 0}",
                    "  call beatit_play"
                ])
            elif isinstance(statement, IRSleep):
                self.expression(statement.amount)
                factor = {"ms": 1, "s": 1000, "min": 60000, "hr": 3600000}[statement.unit or "ms"]
                self.lines.extend([f"  imul rax, {factor}", "  mov rcx, rax", "  call beatit_sleep"])
            elif isinstance(statement, IRFor):
                self.for_loop(statement)
            elif isinstance(statement, IRWhile):
                start, end = self.fresh("while"), self.fresh("endwhile")
                self.lines.append(f"{start}:")
                self.expression(statement.condition)
                self.lines.extend(["  test rax, rax", f"  jz {end}"])
                self.block(statement.body)
                self.lines.extend([f"  jmp {start}", f"{end}:"])
            elif isinstance(statement, IRCall):
                self.call_expr(statement.call)
            elif isinstance(statement, IRReturn):
                if statement.value is not None:
                    self.expression(statement.value)
                else:
                    self.lines.append("  xor eax, eax")
                self.lines.extend(["  add rsp, 32", "  pop rbp", "  ret"])
            elif isinstance(statement, IRVolume):
                self.expression(statement.value)
                self.lines.extend([
                    "  mov rcx, rax",
                    "  call beatit_set_volume"
                ])
            else:
                raise BeatItError(f"Native backend cannot lower {type(statement).__name__}")

    def for_loop(self, statement):
        start, end = self.fresh("for"), self.fresh("endfor")
        loop_counter = self.fresh("loop_idx")
        self.bss.append(f"{loop_counter}: .quad 0")
        limit_var = self.fresh("loop_limit")
        self.bss.append(f"{limit_var}: .quad 0")

        if isinstance(statement.iterable, Range):
            self.expression(statement.iterable.count)
            self.lines.extend([
                f"  mov QWORD PTR [rip + {limit_var}], rax",
                f"  mov QWORD PTR [rip + {loop_counter}], 0",
                f"{start}:",
                f"  mov rax, QWORD PTR [rip + {loop_counter}]",
                f"  cmp rax, QWORD PTR [rip + {limit_var}]",
                f"  jge {end}",
                f"  mov QWORD PTR [rip + var_{statement.variable}], rax",
            ])
        elif isinstance(statement.iterable, Var) and statement.iterable.name in self.lists:
            label, length = self.lists[statement.iterable.name]
            self.lines.extend([
                f"  mov QWORD PTR [rip + {loop_counter}], 0",
                f"{start}:",
                f"  mov rax, QWORD PTR [rip + {loop_counter}]",
                f"  cmp rax, {length}",
                f"  jge {end}",
                f"  lea r8, [rip + {label}]",
                f"  mov rdx, QWORD PTR [rip + {loop_counter}]",
                f"  mov rax, QWORD PTR [r8 + rdx*8]",
                f"  mov QWORD PTR [rip + var_{statement.variable}], rax",
            ])

        else:
            raise BeatItError("Native for-loops require range(n) or a list literal assigned to a variable")
        self.block(statement.body)
        self.lines.extend([
            f"  inc QWORD PTR [rip + {loop_counter}]",
            f"  jmp {start}",
            f"{end}:"
        ])