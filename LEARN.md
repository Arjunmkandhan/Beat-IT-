# Learn Beat It from the inside out

This guide follows the actual code in this checkout. Its goal is for you to be able to change the compiler yourself: make a small language change, then follow that change through every stage.

## What you built

Beat It is a small compiled language for arranging audio. A `.bi` program is not interpreted at playback time. The Python compiler produces native Windows code:

```text
.bi source -> tokens -> AST -> checked AST -> IR -> optimized IR -> x86-64 assembly -> Windows .exe
             lexer      parser    semantic     ir      optimizer       codegen       GCC + C runtime
```

There are two different programs here: the Python compiler runs while building; the generated executable runs later, without Python. The decompiler is separate and only heuristically reconstructs programs emitted by this compiler.

## Start by inspecting, not changing

Run commands from the repository root. Modules use plain imports such as `from lexer import tokenize`, so use the CLI script rather than `python -m beatit.main`.

```powershell
python .\beatit\main.py compile .\sounds.bi --tokens
python .\beatit\main.py compile .\sounds.bi --ast
python .\beatit\main.py compile .\sounds.bi --ir
python .\beatit\main.py compile .\sounds.bi --optimized-ir
python .\beatit\main.py compile .\sounds.bi -o .\build\sounds.exe
.\build\sounds.exe
python .\test_suite2.py
```

The current checkout has a local setup problem: `python` resolves to a pyenv shim with no selected Python version, and `.venv\Scripts` has no `python.exe`. Select/install Python 3.10+ or recreate the virtual environment before running these commands. It is not a missing project dependency: the compiler uses only Python's standard library.

`test_suite2.py` is the current regression script. `test_suite1.py` is an older near-duplicate which expects the old behavior where volume was discarded, so do not treat it as authoritative.

## Beat It language: syntax versus real support

```text
import from sounds as s, sounds.piano_notes as p
volume = 75
kick = s.kick
order = [kick, p.note1]
for beat in order:
    play(beat, 0, 500, ms)
    sleep(100, ms)
count = 0
while count < 3:
    play_async(kick)
    count += 1
int add(a, b):
    return a + b
```

Comments are `//` and `/* ... */`; indentation creates blocks; time units are `ms`, `s`, `min`, and `hr`. Expressions parse integers, decimals, strings, variables, sound paths, lists/indexing, calls, unary `-`, arithmetic and one comparison.

Parsing is broader than compilation. Integer arithmetic, comparisons, variables, sound paths, lists in variables, indexing, `range`, loops, play/sleep/async, volume, and simple function calls work through the native backend. Strings, meaningful fractional arithmetic, true typed `double`/`string` functions, more than four arguments, recursion, independent locals, general iterables, and full return-path checking do not. The backend calls `int()` on numeric values, so `1.5` becomes `1`.

Current source does implement volume, play start/end windows, and `play_async` in the runtime. Async sounds are intentionally non-blocking, but their MCI aliases are not later closed. `main.bi` and `electro_beat.bi` are broad syntax showcases, not safe native smoke tests (they use strings/decimals/richer functions). Start with `sounds.bi`. `beatit/demo.beat` is historical and references missing folders.

## Follow a statement end-to-end

For `play_async(s.kick, 0, 500, ms)`:

1. `lexer.tokenize` creates keyword/operator/identifier/number tokens.
2. `Parser.play_stmt` creates `Play(Qualified("s", "kick"), Num(0), Num(500), "ms", True)`.
3. `SemanticAnalyzer.check_stmt` checks that `s` was imported and the audio asset exists.
4. `IRGenerator.statement` creates `IRPlay`.
5. `Optimizer.block` can fold its constant expressions.
6. `NativeCodeGenerator.block` places the path in `rcx`, start in `rdx`, end in `r8`, async flag in `r9`, then calls `beatit_play`.
7. `native_runtime.c` resolves the path beside the executable and sends Windows MCI an `open` and non-waiting `play` command.

This is the change recipe: for every new construct consider AST class, parser, semantic validation, IR/lowering/formatter, optimizer traversal, backend lowering, runtime support, and tests.

## Repository map

| Path | Purpose | When it runs/helps |
|---|---|---|
| `README.md` | Quick start and support matrix. | When using the project. |
| `LEARN.md` | This detailed guide. | Before changing it. |
| `ARCHITECTURE.md` | Compact technical stage/API map. | During implementation. |
| `WORKING.md` | Development and debugging workflow. | During testing. |
| `AGENTS.md` | Contributor/agent instructions. | Before edits. |
| `requirements.txt` | No pip dependencies; tool requirements. | Environment setup. |
| `sounds.bi` | Small reference source. | Best first trace. |
| `main.bi`, `electro_beat.bi` | Feature demonstrations. | Syntax ideas, not full native tests. |
| `test_suite2.py` | Current self-contained regression runner. | After edits. |
| `test_suite1.py` | Historical duplicate test runner. | Do not rely on stale volume test. |
| `sounds/` | Binary audio assets, including `piano_notes/`. | Copied beside an `.exe`. |
| `build/` | Generated test/build files. | Never hand-edit as source. |
| `*_artifacts/` | Generated/checked-in IR and assembly snapshots. | Learn compiler output. |
| `.vscode/`, `.venv/`, `.gitignore` | Local tooling and Git hygiene. | No compiler logic. |

An audio reference `s.kick` maps to `sounds/kick.<extension>`. Audio files themselves are binary; their bytes are not program logic.

## Every compiler module

### `beatit/ast_nodes.py` — vocabulary shared by every phase

This file only declares dataclasses. Statement nodes are `Program`, `Import`, `Volume`, `Assign`, `AugAssign`, `Play`, `Sleep`, `For`, `While`, `FuncDef`, `Return`, and `CallStmt`. Expression nodes are `Num`, `Str`, `ListLit`, `Var`, `Qualified`, `Index`, `Call`, `BinOp`, `UnaryMinus`, and `Range`. Most include `line` for errors. Add a node here before teaching the compiler a new language form.

### `beatit/lexer.py` — characters to tokens

`KEYWORDS` lists reserved words; `TOKEN_RE` recognizes whitespace, numbers, strings, identifiers, and operators; `Token(kind, value, line)` is the output record. `strip_comments(src)` removes comments while preserving quoted text and newlines, and rejects unclosed block comments. `tokenize(source)` scans lines, tracks nesting depth, converts numbers to Python values, emits indentation/newline/EOF tokens, and rejects bad characters, bracket mismatches, and inconsistent indentation. Add a keyword/operator here only together with parser support and tests.

### `beatit/beat_parser.py` — tokens to AST

`Parser` owns a token cursor. `peek`, `advance`, `at`, `accept`, and `expect` are cursor helpers; `describe` creates readable syntax errors; `end_of_line` requires a newline. `parse_program` loops to EOF. `block` requires colon/newline/indentation. `statement` dispatches and restricts imports/functions to top level.

The statement methods are `import_stmt`, `volume_stmt`, `assignment`, `unit`, `play_stmt`, `sleep_stmt`, `for_stmt`, `while_stmt`, `func_def`, and `return_stmt`. Expression precedence is implemented in this order: `expr` comparison, `additive` plus/minus, `term` multiply/divide, `unary` negation, `postfix` indexing, `primary` literals/lists/variables/qualified paths/calls. `call_expr` parses named calls.

### `beatit/semantic.py` and `assets.py` — check meaning

`SemanticAnalyzer(base_dir)` stores imported module aliases and function definitions. `analyze` first calls `register_import` and collects functions, then validates statements; that first pass permits calls before definitions. `assigned_names` collects assigned names recursively, but is set-based rather than flow-sensitive, so it may allow use-before-assignment. `check_stmt`, `need_var`, `check_call`, and `check_expr` recursively enforce names, arity, basic return rules, top-level volume, modules, and assets.

`assets.py` has `SOUND_EXTENSIONS` (WAV, MP3, AAC, M4A, FLAC, OGG, OPUS, MID/MIDI, WMA) and `find_sound_file(folder, name)`, returning the first real match. Windows MCI codec availability still determines whether a recognised format can play.

### `beatit/ir.py` — a simpler statement form

`IRProgram` separates `globals` from `functions`; `IRFunction` holds a function's name, parameters, body, and declared return type. IR statements are `IRAssign`, `IRAugAssign`, `IRPlay`, `IRSleep`, `IRFor`, `IRWhile`, `IRReturn`, `IRCall`, and `IRVolume`.

`IRGenerator.generate` drops `Import` (compile-time metadata), lowers functions and statements, and keeps expressions as AST nodes. `block` maps statement lists. `format_expr` and `format_ir` render CLI/artifact text; update them whenever adding a node, or diagnostics will lie about the IR.

### `beatit/optimizer.py` — deliberately small optimization

`Optimizer.optimize` deep-copies IR, then processes globals and function bodies. `expression` folds constant unary minus, arithmetic, and comparisons; it leaves division by zero alone. `block` folds relevant fields, removes `while 0`, recurses through loops, and discards statements after a return in the same block. It does not do type analysis, inlining, algebraic simplification, or general dead-store elimination.

### `beatit/native_codegen.py` — IR to assembly

`NativeCodeGenerator(sound_paths)` accumulates instruction `lines`, read-only `data`, zero-initialised `bss`, sound labels, variable names, list layouts, and unique-label counter. `fresh` creates labels; `sound_label` interns paths as `sound_N`; `collect` discovers allocations before code emission.

`generate` emits extern declarations, user functions, then `main`, reserving 32-byte Microsoft x64 ABI shadow space. `function_def` emits `fn_<name>` and stores only four register arguments. `call_expr` evaluates/pushes at most four arguments, pops them into `rcx`, `rdx`, `r8`, `r9`, then calls the generated function.

`expression` emits integer literals, global variables, sound pointers, unary minus, integer arithmetic/comparisons, known-list indexing, and calls. `block` emits assignment/list allocation, playback, sleep, loops, calls, returns, and volume. `for_loop` supports only `range(n)` or a list variable with known layout.

Every source variable and parameter becomes one global `var_<name>` `.bss` slot. Functions with the same name for a local variable share it; recursion overwrites parameter slots. This is the core backend limitation to understand before extending functions.

### `beatit/compiler.py` — pipeline and files

`Compilation` bundles phase results. `find_gcc` finds GCC on PATH/common MinGW locations. `_walk` visits dataclasses/lists. `_sound_paths` resolves AST `Qualified` references to paths relative to the source. `_import_folders` identifies root import folders for copying.

`compile_pipeline(source_file)` validates and reads a `.bi`, then tokenizes, parses, analyses, builds IR, optimizes, generates assembly, and returns `Compilation` without linking. `compile_file` writes `.ir`, `.optimized.ir`, `.s`, invokes GCC with `native_runtime.c` and `-lwinmm`, then copies imported asset folders beside the `.exe`.

### `beatit/native_runtime.c` — Windows audio bridge

This C code is linked into every executable. `g_async_count` makes async MCI aliases unique. `beatit_set_volume` clamps percentage, converts it to two 16-bit channels, and calls `waveOutSetVolume`. `beatit_play(relative, start_ms, end_ms, is_async)` finds the executable directory, opens the file with MCI, sets milliseconds, plays all/from/from-to, waits only for synchronous calls, then closes the synchronous alias. `beatit_sleep(milliseconds)` wraps Windows `Sleep`.

### `beatit/main.py` — CLI

`main(argv=None)` creates the `argparse` interface. Its positional `file` is actually the command (`compile` or `decompile`), while `command_file` is the source/executable. Tokens/AST/IR flags call `compile_pipeline` and return; normal compile calls `compile_file`; `--asm` then prints the `.s`; decompile delegates to `decompile_file`. `BeatItError` and missing files become clean CLI errors.

### `beatit/decompiler.py` — approximate reverse engineering

`find_objdump` locates MinGW objdump. `extract_sound_strings` regex-scans bytes for WAV paths (narrower than `assets.py`). `decompile_file` validates suffix and `MZ` header, extracts paths, optionally runs `objdump -d -M intel`, then recognises labels/instruction patterns from this backend to infer imports, assignments, lists, loops, play, and sleep. Without objdump it emits a basic playback program. Valid generated source is not proof that behavior was recovered.

### Supporting code and tests

`errors.py` defines `BeatItError(message, line=None)` and adds line text to errors. `make_demo_sounds.py` uses standard `wave`, `struct`, `math`, and `random`: `write` serializes mono PCM samples, `tone` creates a decaying sine wave, and `noise` creates decaying noise before its bottom-level demo-file calls.

Both test files are direct Python scripts, not pytest. Their `test`, `expect_error`, `parse_src`, `gen_ir`, and `gen_asm` helpers test every phase plus GCC/decompilation. `test_suite2.py` is the updated version and creates expected temporary output in `build/`.

## Exactly what executes during a build

```text
main.main -> compiler.compile_file -> compile_pipeline
source -> Token[] -> Program AST -> SemanticAnalyzer -> IR -> Optimizer -> NativeCodeGenerator
       -> write build/name_artifacts/name.{ir,optimized.ir,s}
       -> gcc name.s native_runtime.c -lwinmm -o name.exe
       -> copy imported audio folders beside name.exe

Later: name.exe -> generated main -> beatit_set_volume/play/sleep -> Windows MCI/waveOut -> audio
```

The executable contains paths, not embedded audio. Keep copied `sounds/` folders alongside it when moving it.

## How to change the project yourself

For a new statement or expression:

1. Define exact syntax and limitations.
2. Update lexer only if new tokens/keywords are required.
3. Add AST node(s) in `ast_nodes.py`.
4. Parse in `beat_parser.py`; add parser tests.
5. Validate in `semantic.py`.
6. Add/lower/format an IR node in `ir.py`.
7. Teach optimizer traversal/transformation if relevant.
8. Emit assembly in `native_codegen.py`.
9. Add a C runtime function if the feature needs Windows services.
10. Add focused and full-pipeline tests to `test_suite2.py`.
11. Update all four project docs.

For a backend bug, start at the failed AST/IR form and go forward. For a syntax bug, start at source characters and go forward. Never say a feature works just because it parses: compile it, and run the output for audio behavior.

## Technical debt to tackle next

- Package-relative imports and `beatit/__init__.py`.
- Stack frames/per-function variable scopes instead of global slots.
- Real type checking, or a grammar narrowed to backend support.
- Reject fractional numbers until real floating-point lowering exists.
- Close/manage asynchronous MCI aliases.
- Align decompiler extensions with `assets.py` and parse PE sections.
- Remove the duplicate test suite and use a standard test runner.
