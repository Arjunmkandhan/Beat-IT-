# Beat It: compiler architecture

This document describes the implementation in `beatit\*.py` and `beatit\native_runtime.c`. The implementation is a Windows native compiler with an experimental decompiler; it is not an interpreter.

## End-to-end flow

```text
.bi source
  -> lexer.tokenize
  -> Parser.parse_program -> AST
  -> SemanticAnalyzer.analyze
  -> IRGenerator.generate -> IRProgram
  -> Optimizer.optimize
  -> NativeCodeGenerator.generate -> GAS Intel-syntax assembly
  -> GCC + native_runtime.c + -lwinmm -> Windows executable
```

`compiler.compile_pipeline()` performs the source-to-assembly stages in memory. `compiler.compile_file()` writes `.ir`, `.optimized.ir`, and `.s` artifacts, invokes GCC, and copies imported asset directories next to the output executable. The source is not embedded in the executable. `decompiler.py` is a separate heuristic utility and is not part of this forward pipeline.

## Front end

### Lexing: `lexer.py`

`tokenize(source)` first calls `strip_comments()`, then scans lines using a regular expression. Tokens include integer and decimal numeric literals, strings, identifiers, keywords, operators, newlines, indentation changes, and EOF. An indentation stack emits `INDENT` and `DEDENT`; nested parentheses and square brackets suppress line breaks while an expression continues. Line comments use `//`; block comments use `/* ... */`.

The lexer reports unexpected characters, unmatched closing delimiters, unclosed delimiters, inconsistent indentation, and unterminated block comments through `BeatItError`.

### Parsing and AST: `beat_parser.py`, `ast_nodes.py`

`Parser.parse_program()` dispatches statements until EOF. Blocks are colon + newline + indented statements. Expression parsing is recursive descent with precedence:

```text
comparison -> addition/subtraction -> multiplication/division
           -> unary minus -> indexing -> primary
```

Comparisons are limited to one per expression. The AST is made of dataclasses for imports, assignments, playback, loops, functions, returns, calls, literals, lists, indexing, and operators.

The grammar recognizes `int`, `double`, `string`, and `void` function declarations; parameters are untyped names. `play` accepts optional start/end/unit syntax, and `volume = expression` is a statement. These syntax features are not all implemented by the native backend.

## Semantic analysis: `semantic.py`, `assets.py`

`SemanticAnalyzer.analyze()` first registers top-level imports and function declarations, then walks statements and expressions to check them. Imports resolve folders relative to the source file. An imported sound reference must resolve to a file named `<sound>.wav`; `assets.SOUND_EXTENSIONS` currently contains only `.wav`.

Checks include duplicate import aliases and function names, unresolved variables/modules/functions, call argument counts, use of a `void` call as a value, return outside a function, and the presence/absence of return expressions based on `void` versus non-`void`. `volume` must be top-level.

This is not a full type checker. `assigned_names()` collects names into sets rather than performing ordered, flow-sensitive definite-assignment analysis. The analyzer does not infer expression types or prove that every path in a non-void function returns.

## Intermediate representation: `ir.py`

`IRGenerator` drops imports and `Volume` statements, separates functions from global statements, and lowers remaining statements into `IRProgram(globals, functions)`. IR nodes represent assignment, augmented assignment, playback, sleep, loops, calls, and returns. Expressions remain AST expression nodes. `format_ir()` provides the textual form used by CLI inspection and artifact files.

Because `Volume` is discarded here, a `volume = ...` statement has no effect on generated programs.

## Optimization: `optimizer.py`

`Optimizer.optimize()` deep-copies the IR and recursively processes global/function blocks. It:

- Folds numeric unary minus and constant arithmetic/comparisons.
- Leaves division-by-zero expressions unfolded.
- Removes a `while` whose condition folds to false.
- Removes statements after an unconditional `return` in the same block.

It does not implement general dead-store elimination, algebraic simplification, or broad control-flow optimization.

## Native backend: `native_codegen.py`

`NativeCodeGenerator` emits GAS-compatible Intel syntax, `.rdata` sound-path strings, `.bss` storage, a `main` entry point, and function/loop labels. Variables are memory-backed. Arithmetic and comparisons are lowered to integer x86-64 operations; `beatit_play` and `beatit_sleep` receive their first argument in `rcx`.

Sound expressions become pointers to paths relative to the source directory. Lists are emitted as fixed-size arrays; list assignment initializes their entries. `for` generation supports `range(count)` and a list variable recognized by the generator. `while` loops branch on an integer condition.

Native backend constraints:

- `Num` must have a whole-number value; a decimal such as `1.5` raises `BeatItError`, while `1.0` is emitted as integer `1`.
- `Str` and other unsupported expression nodes cannot be lowered.
- `play` lowering evaluates and passes only `beat`; parsed `start`, `end`, and `unit` fields are ignored.
- `for` only handles `Range` or a previously recognized list variable.
- Calls use the first four arguments in `rcx`, `rdx`, `r8`, and `r9`; additional arguments are not passed.
- All user variables, including function parameters, are emitted in global storage. Calls are not reentrant and recursive/local-variable semantics are not implemented.
- Function signatures are not type-lowered. A non-void function that reaches the end returns zero from the generated epilogue.

These are current implementation constraints, not claims about the parser grammar.

## Linker and runtime: `compiler.py`, `native_runtime.c`

The compiler finds MinGW GCC on `PATH` or in common installation folders, then runs it with the assembly, the fixed C runtime, and `-lwinmm`. The executable is a Windows PE binary. Imported sound folders are copied next to the executable, preserving relative paths. The C runtime builds the path from the executable directory and calls `PlaySoundA(..., SND_FILENAME | SND_SYNC)`; playback is synchronous. `beatit_sleep()` delegates to Windows `Sleep()`.

The runtime does not mix concurrent audio, implement volume control, or crop playback to a specified time window.

## CLI: `main.py`

The CLI supports:

```text
python beatit/main.py compile source.bi [-o output.exe] [--emit-dir directory]
python beatit/main.py compile source.bi --tokens|--ast|--ir|--optimized-ir
python beatit/main.py compile source.bi --asm
python beatit/main.py decompile program.exe [-o output.bi]
```

Phase-inspection flags call `compile_pipeline()` and return without linking. `--asm` performs a normal executable build and then prints its assembly artifact. `BeatItError` and missing input files are rendered as CLI errors.

## Heuristic decompiler: `decompiler.py`

The decompiler validates the DOS `MZ` prefix, scans the entire executable byte stream for strings ending in `.wav`, and optionally invokes `objdump -d -M intel`. It searches the disassembly text for expected generated labels/instruction patterns to infer assignments, lists, loops, playback, and sleep calls. If disassembly is unavailable, it writes a simple sound-list example based on discovered paths.

This is pattern-based reconstruction, not a general x86 disassembler or PE-section parser. It may lose expressions, control flow, functions, timing details, or other source semantics. A successfully written `.bi` file is not proof that the original source was recovered faithfully.

## Remaining modules

| Module | Responsibility |
|---|---|
| `errors.py` | `BeatItError`, optionally annotated with a source line |
| `make_demo_sounds.py` | Generates synthetic mono PCM WAV examples |
| `demo.beat` | Additional syntax example; the primary project source example is `main.bi` |
