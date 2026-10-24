# Beat It: a native audio-language compiler

Beat It is a small, indentation-based language for sequencing WAV samples. Its Python toolchain tokenizes and parses `.bi` source, checks names and assets, generates an intermediate representation (IR), optimizes that IR, emits x86-64 assembly, and links a Windows executable. The generated program does not run Python; it calls a small C runtime that uses Windows `PlaySoundA` and `Sleep`.

The project also includes an experimental decompiler. It scans executable bytes for WAV paths and uses `objdump` output patterns to heuristically reconstruct some source constructs. It is not a general-purpose or lossless decompiler.

## Requirements

- Python 3.10 or newer.
- MinGW-w64 GCC on `PATH` to compile an executable. The compiler also checks several common Windows MinGW installation paths.
- `objdump` on `PATH` for machine-code-based decompilation. If unavailable or disassembly fails, the decompiler can only emit a simple program based on detected sound paths.
- WAV files for imported sounds. The current asset resolver recognizes `.wav` only.

The Python compiler uses the standard library. `requirements.txt` has no runtime packages to install.

## Compile and run

From the project root in PowerShell:

```powershell
python .\beatit\main.py compile .\main.bi -o .\build\main.exe
```
Now Run the Executable file : 
```
.\build\main.exe
```

Compilation writes the executable, copies the imported sound folders beside it, and creates IR, optimized-IR, and assembly artifacts under `build\main_artifacts\`. The executable is Windows-specific.

To decompile:

```powershell
python .\beatit\main.py decompile .\build\main.exe -o .\build\restored.bi
```

Decompilation is heuristic. Reconstructed source may omit or misrepresent behavior, so inspect it before relying on it or recompiling it.

## Inspect compiler output

These commands run the front end and native code generation pipeline up through assembly generation; they do not link an executable:

```powershell
python .\beatit\main.py compile .\main.bi --tokens
python .\beatit\main.py compile .\main.bi --ast
python .\beatit\main.py compile .\main.bi --ir
python .\beatit\main.py compile .\main.bi --optimized-ir
```

`--asm` performs a normal compile, then prints the generated assembly. `-o` selects the executable path and `--emit-dir` selects the artifact directory.

## Language example

Imports are folders relative to the source file. A sound such as `s.kick` resolves to `sounds\kick.wav`.

```text
import from sounds as s

kick = s.kick
snare = s.snare
order = [kick, snare]

for beat in order:
    play(beat)

count = 0
while count < 3:
    play(kick)
    sleep(200, ms)
    count += 1
```

The parser also recognizes numeric expressions, comparisons, indexing, function declarations/calls, `volume = ...`, and optional playback-window arguments. Recognition by the parser does not guarantee backend support; see [implementation limits](#implementation-limits).

## Compiler stages

1. `lexer.py` tokenizes source, strips comments, and emits indentation tokens.
2. `beat_parser.py` and `ast_nodes.py` build an AST with a recursive-descent parser.
3. `semantic.py` validates imports, referenced WAV files, variables, function names/arity, and return-statement rules.
4. `ir.py` lowers statements into a linear, structured IR.
5. `optimizer.py` folds constant arithmetic/comparisons, removes statically false `while` loops, and stops a block after `return`.
6. `native_codegen.py` emits Intel-syntax x86-64 assembly.
7. `compiler.py` invokes GCC to assemble/link the generated assembly with `native_runtime.c` and `-lwinmm`.

`decompiler.py` is a separate reverse-engineering utility; it is not a compiler phase.

## Implementation limits

The parser accepts more forms than the current native backend can compile. In particular:

- Native numeric literals must have whole-number values; a decimal such as `1.5` is rejected, while `1.0` is emitted as integer `1` rather than as floating point.
- String expressions are parsed but are not lowered by the native backend.
- `volume` is accepted and checked at top level, but the IR generator drops it, so it has no effect in the executable.
- `play(beat, start, end, unit)` is parsed, but generated code currently passes only the sound path; start/end window arguments are ignored.
- Native `for` loops support `range(n)` or a list assigned to a variable. Other iterables are not implemented.
- Generated function calls pass at most four arguments. Function parameters and variables use global storage, so this backend does not implement independent local stack frames or reliable recursion.
- The semantic analyzer checks names and function-call arity, not general expression types or all control-flow return paths.

The native runtime calls `PlaySoundA` with `SND_SYNC`, so each `play` waits for the WAV to finish. It does not mix overlapping sounds. `sleep` uses Windows `Sleep`; its default unit is milliseconds. Supported units are `ms`, `s`, `min`, and `hr`.

## Project files

| Path | Purpose |
|---|---|
| `beatit/main.py` | CLI for compile, decompile, and phase inspection |
| `beatit/lexer.py` | Lexer and comment stripping |
| `beatit/beat_parser.py`, `beatit/ast_nodes.py` | Parser, grammar, and AST dataclasses |
| `beatit/semantic.py`, `beatit/assets.py` | Name/function/import checks and WAV lookup |
| `beatit/ir.py` | IR nodes, lowering, and IR formatter |
| `beatit/optimizer.py` | Small IR optimization pass |
| `beatit/native_codegen.py` | x86-64 assembly backend |
| `beatit/compiler.py` | Compiler orchestration, artifacts, GCC invocation, asset packaging |
| `beatit/native_runtime.c` | Windows WAV playback and sleep functions |
| `beatit/decompiler.py` | Heuristic executable-to-source reconstruction |
| `beatit/errors.py` | User-facing compiler diagnostic type |
| `beatit/make_demo_sounds.py` | Generator for small example WAV files |
| `main.bi` | Example program |
| `sounds\` | WAV assets referenced by `main.bi` |
