# Beat It implementation guide

This guide follows the current Python source in `beatit\`. It supersedes older notes describing `interpreter.py`, `audio.py`, pygame, or a Python playback engine: those modules are not present. The current implementation compiles supported Beat It programs to Windows executables.

## 1. What happens during compilation

The CLI is `beatit\main.py`:

```powershell
python .\beatit\main.py compile .\main.bi -o .\build\main.exe
```

The flow is:

1. `main.main()` parses the `compile` command and calls `compiler.compile_pipeline()`.
2. `lexer.tokenize()` strips comments and produces tokens.
3. `Parser.parse_program()` builds an AST.
4. `SemanticAnalyzer.analyze()` checks imports, symbols, functions, and sound files.
5. `IRGenerator.generate()` builds IR; `Optimizer.optimize()` folds eligible constants.
6. `NativeCodeGenerator.generate()` emits assembly.
7. `compile_file()` writes the assembly and IR artifacts, invokes MinGW GCC with `native_runtime.c` and `-lwinmm`, and copies imported sound folders beside the executable.

`compile_pipeline()` does not invoke GCC. Inspection flags use this path and stop after printing their selected output. The `--asm` flag is different: it compiles the executable and then prints its assembly artifact.

The generated program contains native code and the fixed C runtime, not Python source or a Python interpreter.

## 2. Walkthrough of `main.bi`

The example imports `sounds`, binds four named WAV sounds to variables, constructs a list, and loops over that list to call `play`.

- The parser represents each sound reference such as `s.C_OldiscoPiano_02_728` as a `Qualified` expression.
- The semantic analyzer checks that `sounds\` exists beside `main.bi` and that each referenced name has a matching `.wav`.
- The IR generator lowers the assignments and loop; imports are omitted because they are compile-time metadata.
- The backend emits string pointers for the sound paths, global variables, a fixed-size array for `order`, and a loop that reads list entries.
- `play(i)` calls the C runtime, which uses synchronous `PlaySoundA`.

`count = 0` remains a normal assignment even though the sample does not subsequently use it.

## 3. Lexer: `lexer.py`

### `strip_comments(src)`

Walks characters while tracking whether it is inside a quoted string. It removes `//` comments and `/* ... */` comments while keeping newline counts for useful source line numbers. An unterminated block comment raises `BeatItError`.

### `tokenize(source)`

Uses a regular expression for whitespace, decimals, integers, quoted strings, identifiers, and operators. Identifiers in `KEYWORDS` become `KEYWORD`; all others become `IDENT`. Numeric token values are Python `int` or `float`, and string delimiters are removed.

An indentation-width stack emits `INDENT` and `DEDENT`. Bracket depth suppresses logical newlines inside parentheses and lists. The lexer rejects unexpected characters, inconsistent indentation, unmatched closing brackets, and unclosed brackets. Tabs are expanded to width four for indentation measurement.

## 4. Parser and AST: `beat_parser.py`, `ast_nodes.py`

`Parser` maintains a token cursor. `peek`, `advance`, `at`, `accept`, and `expect` are its token helpers; `expect` raises a line-aware `BeatItError` when syntax does not match.

`parse_program()` repeatedly calls `statement(top=True)`. `block()` parses a colon, newline, indent, statements, and dedent. Imports and function definitions are restricted to top level.

The expression precedence, from lowest to highest, is:

```text
one comparison -> + and - -> * and / -> unary minus -> indexing -> primary
```

Comparison chaining is not supported. The parser recognizes:

- Imports with dotted paths and optional aliases.
- Assignment (`=`) and augmented addition (`+=`).
- `play(...)`, `sleep(...)`, `for`, `while`, `return`, and function calls.
- Function declarations using `int`, `double`, `string`, or `void`; parameter names have no declared types.
- Integer/decimal/string literals, lists, indexing, qualified sound references, calls, and arithmetic/comparison expressions.

`ast_nodes.py` defines dataclasses for those constructs: `Program`, `Import`, `Volume`, `Assign`, `AugAssign`, `Play`, `Sleep`, `For`, `While`, `FuncDef`, `Return`, `CallStmt`, and expression nodes (`Num`, `Str`, `ListLit`, `Var`, `Qualified`, `Index`, `Call`, `BinOp`, `UnaryMinus`, `Range`).

## 5. Semantic analysis: `semantic.py`, `assets.py`

`SemanticAnalyzer.analyze()` makes two passes:

1. Register imports and top-level function signatures, rejecting duplicate aliases and duplicate function names.
2. Check statements and expressions using names collected from assignments and loop variables.

It checks that import directories exist next to the source file, sound references use imported modules and resolve to assets, variables and functions are known, function calls have the declared number of arguments, and return statements follow basic `void`/non-`void` rules. A `void` function call cannot be used as an expression. `volume` is allowed only at top level.

`assets.find_sound_file()` checks exactly `<name>.wav`. General expression type checking is not implemented. Name collection is set-based, not flow-sensitive; it does not reliably catch use before assignment or prove that all paths of a typed function return.

## 6. IR and optimizer: `ir.py`, `optimizer.py`

The IR consists of `IRProgram(globals, functions)`, `IRFunction`, and statement nodes for assignments, augmented assignments, play, sleep, loops, calls, and returns. `IRGenerator` lowers AST statements but leaves expressions in AST form. Imports and `Volume` statements are discarded.

`format_ir()` emits readable source-like IR, for example:

```text
order = [beat1, beat3]
FOR i IN order:
  PLAY i
```

The optimizer deep-copies the program. It recursively folds constant unary-minus, arithmetic, and comparison expressions. It leaves division-by-zero expressions unchanged, removes `while` loops with a constant false condition, and removes statements after a return in that same block. It is intentionally small; it does not implement general dead-store analysis or algebraic simplification.

## 7. Native code generation: `native_codegen.py`

The backend emits Intel-syntax assembly for GCC. It collects variable names into `.bss`, places sound paths in `.rdata`, emits user functions, then emits `main`. Generated expressions use integer registers and memory-backed variables. `sleep` converts its unit to milliseconds before calling `beatit_sleep`; `play` calls `beatit_play` with a path pointer.

Supported native constructs include integer arithmetic/comparisons, variables, sound references, unary minus, indexing of generated list variables, up-to-four-argument function calls, `play`, `sleep`, `while`, and `for` loops over `range(n)` or a list variable.

Known limits matter when interpreting the grammar:

- Decimal-valued numbers are rejected unless their numeric value is whole; for example, `1.5` fails but `1.0` is emitted as integer `1`.
- String values are not implemented by code generation.
- `volume` is dropped during IR generation and does nothing.
- Optional `play` start/end/unit values are parsed but ignored by code generation.
- Other iterable forms for `for` produce a backend error.
- Function parameters and other variables are global storage slots, not isolated locals. The generated backend therefore does not provide reliable recursion or independent function-local state.
- Calls only pass the first four parameters. The backend does not implement typed calling conventions for `double` or `string`.
- Non-void functions that fall through return zero from their generated epilogue.

## 8. Linking and audio runtime

`compiler.find_gcc()` checks `PATH` and common MinGW folders. `compile_file()` invokes GCC with the generated `.s`, `native_runtime.c`, `-lwinmm`, and the requested `.exe` path. It writes `.ir`, `.optimized.ir`, and `.s` artifacts and copies imported folders to the output directory, preserving their relative path.

`native_runtime.c` implements:

- `beatit_play(relative)`: derives the executable folder, appends the relative path, and calls `PlaySoundA` with `SND_FILENAME | SND_SYNC`.
- `beatit_sleep(milliseconds)`: calls Windows `Sleep`.

Because playback is synchronous, each sound completes before the next `play` call continues. No mixer or overlap is implemented. Sleep units in the language are `ms` (default), `s`, `min`, and `hr`.

## 9. Decompiler: `decompiler.py`

`decompile_file()` checks for an `.exe` with an `MZ` prefix. It searches the entire byte stream for strings ending in `.wav`, then tries to run `objdump -d -M intel`. Regular expressions look for expected labels and instruction patterns emitted by this compiler to infer some assignments, lists, loops, play calls, and sleeps.

When no disassembly is available, it can emit only a basic example derived from recovered asset paths. The decompiler is heuristic and not lossless: it does not parse the PE section table and cannot reliably reconstruct arbitrary machine code or all source semantics.

## 10. CLI and supporting modules

| File | Role |
|---|---|
| `main.py` | Parses `compile`/`decompile`, phase flags, output and artifact-directory options |
| `errors.py` | `BeatItError` with an optional source line |
| `make_demo_sounds.py` | Generates simple synthetic WAV files |
| `demo.beat` | Broader syntax example; some constructs in it exceed current native backend support |

Commands:

```powershell
python .\beatit\main.py compile .\main.bi --tokens
python .\beatit\main.py compile .\main.bi --ast
python .\beatit\main.py compile .\main.bi --ir
python .\beatit\main.py compile .\main.bi --optimized-ir
python .\beatit\main.py compile .\main.bi --asm
python .\beatit\main.py decompile .\build\main.exe -o .\build\restored.bi
```

## 11. Important distinctions

- **Parsed does not mean compiled:** the grammar is broader than the native backend.
- **Semantic checking is not full type checking:** some unsupported values fail later during code generation.
- **Decompilation is approximate:** valid output syntax does not mean recovered behavior is equivalent.
- **The generated program is Windows-specific:** it requires the Windows multimedia APIs and MinGW at build time.
