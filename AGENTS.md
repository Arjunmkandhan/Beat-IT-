# Beat It contributor guide

Beat It compiles its indentation-based `.bi` audio language into a Windows x86-64 executable. The pipeline is `lexer -> parser/AST -> semantic analysis -> IR -> optimizer -> assembly -> GCC/native runtime`.

Read `LEARN.md` before changing compiler behavior. Use `python .\beatit\main.py compile .\sounds.bi --ir` to inspect phases without linking. `compiler.compile_pipeline()` stops after assembly generation; `compile_file()` writes artifacts, links with MinGW-w64 GCC, and copies imported audio directories next to the executable.

`test_suite2.py` is the current regression runner and needs Python, MinGW GCC, and objdump for full coverage. `test_suite1.py` is historical and has stale volume expectations.

When adding a language feature, normally update AST, parser, semantic analysis, IR/formatter, optimizer traversal, native backend, C runtime when needed, tests, and docs. Parsing alone does not mean native support. Put generated outputs in `build/`; do not hand-edit `.ir`, `.optimized.ir`, `.s`, or `.exe` files.

Current facts: volume/start-end playback windows/async are implemented; decimals truncate in native lowering; strings and robust floating-point semantics are not implemented; functions share global variable storage and pass only four arguments; decompilation is heuristic. Update `README.md`, `ARCHITECTURE.md`, `WORKING.md`, and `LEARN.md` with any user-visible behavior or limitation change.





