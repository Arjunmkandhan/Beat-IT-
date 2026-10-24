"""Native Beat It compiler orchestration (phases 1 through 7)."""
from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ast_nodes import Qualified, Import
from beat_parser import Parser
from errors import BeatItError
from ir import IRGenerator, format_ir
from lexer import tokenize
from native_codegen import NativeCodeGenerator
from optimizer import Optimizer
from semantic import SemanticAnalyzer
from assets import find_sound_file


@dataclass
class Compilation:
    source: Path
    tokens: list
    ast: object
    analyzer: SemanticAnalyzer
    ir: object
    optimized_ir: object
    asm_source: str


def find_gcc() -> str:
    path = shutil.which("gcc")
    if path:
        return path
    candidates = [
        r"C:\Program Files\CodeBlocks\MinGW\bin\gcc.exe",
        r"C:\MinGW\bin\gcc.exe",
        r"C:\msys64\mingw64\bin\gcc.exe",
        r"C:\msys64\ucrt64\bin\gcc.exe",
        r"C:\TDM-GCC-64\bin\gcc.exe",
    ]
    for c in candidates:
        if Path(c).is_file():
            bin_dir = str(Path(c).parent)
            if bin_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
            return c
    raise BeatItError("Native compilation needs MinGW-w64 GCC on PATH (gcc.exe)")


def _walk(value):
    if isinstance(value, list):
        for item in value:
            yield from _walk(item)
    elif hasattr(value, "__dataclass_fields__"):
        yield value
        for name in value.__dataclass_fields__:
            yield from _walk(getattr(value, name))


def _sound_paths(program, analyzer, source_dir):
    paths = {}
    for node in _walk(program):
        if isinstance(node, Qualified):
            actual = find_sound_file(analyzer.modules[node.module], node.sound)
            paths[(node.module, node.sound)] = actual.resolve().relative_to(source_dir.resolve()).as_posix()
    return paths


def _import_folders(program, source_dir):
    folders = {Path(*path) for statement in program.body if isinstance(statement, Import)
               for path, _alias in statement.items}
    roots = [path for path in folders if not any(parent != path and parent in path.parents for parent in folders)]
    return [(path, source_dir / path) for path in roots]


def compile_pipeline(source_file):
    """Run phases 1–6 in memory. Useful for tests and inspection flags."""
    source = Path(source_file).resolve()
    if source.suffix.lower() != ".bi":
        raise BeatItError("Native compiler input must be a .bi file")
    if not source.is_file():
        raise FileNotFoundError(source)
    tokens = tokenize(source.read_text(encoding="utf-8"))
    ast = Parser(tokens).parse_program()
    analyzer = SemanticAnalyzer(source.parent)
    analyzer.analyze(ast)
    ir = IRGenerator().generate(ast)
    optimized_ir = Optimizer().optimize(ir)
    asm_source = NativeCodeGenerator(_sound_paths(ast, analyzer, source.parent)).generate(optimized_ir)
    return Compilation(source, tokens, ast, analyzer, ir, optimized_ir, asm_source)


def compile_file(source_file, output_file=None, artifact_dir=None):
    """Run all 7 phases and link a native Windows executable with MinGW GCC.
    
    Phases:
      1. Lexical Analysis (lexer.py)
      2. Syntax Analysis (beat_parser.py)
      3. Semantic Analysis (semantic.py)
      4. Intermediate Code Generation (ir.py)
      5. Code Optimization (optimizer.py)
      6. Native Code Generation (native_codegen.py -> x86-64 assembly)
      7. Assembly & Linking (compiler.py + native_runtime.c -> Windows .exe)
    """
    build = compile_pipeline(source_file)
    output = Path(output_file) if output_file else build.source.with_suffix(".exe")
    output = output.resolve().with_suffix(".exe")
    output.parent.mkdir(parents=True, exist_ok=True)
    artifacts = Path(artifact_dir).resolve() if artifact_dir else output.parent / f"{output.stem}_artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)

    asm_file = artifacts / f"{output.stem}.s"
    asm_file.write_text(build.asm_source, encoding="utf-8")
    (artifacts / f"{output.stem}.ir").write_text(format_ir(build.ir) + "\n", encoding="utf-8")
    (artifacts / f"{output.stem}.optimized.ir").write_text(format_ir(build.optimized_ir) + "\n", encoding="utf-8")

    gcc = find_gcc()
    runtime_c = Path(__file__).parent / "native_runtime.c"
    if not runtime_c.is_file():
        raise BeatItError(f"Native runtime library not found at {runtime_c}")

    try:
        # Assemble our Phase 6 generated assembly (.s) and link with native runtime (.c)
        subprocess.run(
            [gcc, str(asm_file), str(runtime_c), "-lwinmm", "-o", str(output)],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip().splitlines()[-1] if error.stderr else "unknown GCC error"
        raise BeatItError(f"Native backend assembly/linking failed: {detail}") from error

    # Copy imported sound folders next to the target executable so it can be run standalone
    for relative, folder in _import_folders(build.ast, build.source.parent):
        destination = output.parent / relative
        if folder.resolve() != destination.resolve():
            shutil.copytree(folder, destination, dirs_exist_ok=True)

    # NOTE: We deliberately do NOT embed the source code in the executable.
    # The executable is a pure native binary.
    return output, artifacts

