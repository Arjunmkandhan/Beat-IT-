"""Comprehensive test suite for Beat It compiler.
Tests all phases: lexer, parser, semantic analysis, IR generation, optimization, codegen, decompiler.
Run from project root: python test_suite.py
"""
import sys
import traceback
import tempfile
from pathlib import Path

# Add beatit folder to path
sys.path.insert(0, str(Path(__file__).parent / "beatit"))

from lexer import tokenize
from beat_parser import Parser
from ir import IRGenerator, format_ir
from ast_nodes import FuncDef, Import
from errors import BeatItError
from optimizer import Optimizer
from semantic import SemanticAnalyzer
from native_codegen import NativeCodeGenerator
from compiler import compile_pipeline, compile_file
from decompiler import decompile_file, extract_sound_strings

GREEN = "\033[92m"
RED   = "\033[91m"
RESET = "\033[0m"
BOLD  = "\033[1m"

passed = 0
failed = 0
errors = []


def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  [{GREEN}PASS{RESET}] {name}")
        passed += 1
    except Exception as exc:
        print(f"  [{RED}FAIL{RESET}] {name}")
        tb = traceback.format_exc()
        errors.append((name, str(exc), tb))
        failed += 1


def expect_error(fn, msg_contains=None):
    """Assert fn() raises BeatItError. Optionally check message substring."""
    try:
        fn()
        raise AssertionError("Expected BeatItError but no error was raised")
    except BeatItError as exc:
        if msg_contains and msg_contains.lower() not in str(exc).lower():
            raise AssertionError(
                f"Wrong error. Got: {exc!r}  Expected substring: {msg_contains!r}"
            )


def parse_src(src):
    return Parser(tokenize(src)).parse_program()


def gen_ir(src):
    return IRGenerator().generate(parse_src(src))


def gen_asm(src, sound_paths=None):
    ir = Optimizer().optimize(gen_ir(src))
    return NativeCodeGenerator(sound_paths or {}).generate(ir)


BASE = Path(__file__).parent


# =============================================================================
# PHASE 1: LEXER
# =============================================================================
print(f"\n{BOLD}=== PHASE 1: LEXER ==={RESET}")


def t_lex_basic():
    toks = tokenize("x = 42")
    kinds = [t.kind for t in toks]
    assert kinds == ["IDENT", "OP", "INT", "NEWLINE", "EOF"], f"Got {kinds}"


def t_lex_string():
    toks = tokenize('"hello world"')
    assert toks[0].kind == "STRING" and toks[0].value == "hello world"


def t_lex_float():
    toks = tokenize("3.14")
    assert toks[0].kind == "DOUBLE"
    assert abs(toks[0].value - 3.14) < 1e-9


def t_lex_keywords():
    toks = tokenize("for i in range(3):")
    kws = [t.value for t in toks if t.kind == "KEYWORD"]
    assert "for" in kws and "in" in kws and "range" in kws


def t_lex_indent_dedent():
    toks = tokenize("for i in range(3):\n    x = 1\nx = 2")
    kinds = [t.kind for t in toks]
    assert "INDENT" in kinds and "DEDENT" in kinds


def t_lex_line_comment():
    toks = tokenize("x = 1 // comment\ny = 2")
    idents = [t.value for t in toks if t.kind == "IDENT"]
    assert idents == ["x", "y"]


def t_lex_block_comment():
    toks = tokenize("x = 1\n/* block\ncomment */\ny = 2")
    idents = [t.value for t in toks if t.kind == "IDENT"]
    assert idents == ["x", "y"]


def t_lex_aug_assign():
    toks = tokenize("count += 1")
    ops = [t.value for t in toks if t.kind == "OP"]
    assert "+=" in ops


def t_lex_comparison_ops():
    for op in ["==", "!=", "<=", ">=", "<", ">"]:
        toks = tokenize(f"a {op} b")
        ops = [t.value for t in toks if t.kind == "OP"]
        assert op in ops, f"Operator {op!r} missing"


def t_lex_unterminated_comment():
    expect_error(lambda: tokenize("/* never closed"), "unterminated")


def t_lex_parens_suppress_newline():
    toks = tokenize("play(\n    i\n)")
    assert [t.kind for t in toks].count("NEWLINE") == 1


test("Basic assignment tokens", t_lex_basic)
test("String literal token", t_lex_string)
test("Float literal token", t_lex_float)
test("Keywords tokenized correctly", t_lex_keywords)
test("INDENT / DEDENT emitted", t_lex_indent_dedent)
test("Line comment stripped", t_lex_line_comment)
test("Block comment stripped", t_lex_block_comment)
test("Augmented assign += tokenized", t_lex_aug_assign)
test("Comparison operators tokenized", t_lex_comparison_ops)
test("Unterminated block comment raises error", t_lex_unterminated_comment)
test("Parens suppress interior NEWLINE tokens", t_lex_parens_suppress_newline)


# =============================================================================
# PHASE 2: PARSER
# =============================================================================
print(f"\n{BOLD}=== PHASE 2: PARSER ==={RESET}")


def t_parse_assign():
    from ast_nodes import Assign, Num
    node = parse_src("x = 5").body[0]
    assert isinstance(node, Assign) and isinstance(node.value, Num)


def t_parse_augassign():
    from ast_nodes import AugAssign
    node = parse_src("count = 0\ncount += 3").body[1]
    assert isinstance(node, AugAssign) and node.op == "+"


def t_parse_for_range():
    from ast_nodes import For, Range
    node = parse_src("for i in range(5):\n    x = i").body[0]
    assert isinstance(node, For) and isinstance(node.iterable, Range)


def t_parse_for_list():
    from ast_nodes import For, Var
    node = parse_src("x = [1, 2, 3]\nfor i in x:\n    y = i").body[1]
    assert isinstance(node, For) and isinstance(node.iterable, Var)


def t_parse_while():
    from ast_nodes import While, BinOp
    node = parse_src("count = 0\nwhile count < 3:\n    count += 1").body[1]
    assert isinstance(node, While) and isinstance(node.cond, BinOp)


def t_parse_func_def():
    node = parse_src("void myFunc(a, b):\n    x = a").body[0]
    assert isinstance(node, FuncDef)
    assert node.name == "myFunc" and node.params == ["a", "b"]
    assert node.ret_type == "void"


def t_parse_return():
    from ast_nodes import Return
    body = parse_src("int add(a, b):\n    return a").body[0].body
    assert isinstance(body[0], Return)


def t_parse_play():
    from ast_nodes import Play
    assert isinstance(parse_src("play(x)").body[0], Play)


def t_parse_sleep():
    from ast_nodes import Sleep
    assert isinstance(parse_src("sleep(500)").body[0], Sleep)


def t_parse_binop_precedence():
    from ast_nodes import BinOp
    val = parse_src("x = 2 + 3 * 4").body[0].value
    assert isinstance(val, BinOp) and val.op == "+"


def t_parse_unary_minus():
    from ast_nodes import UnaryMinus
    val = parse_src("x = -5").body[0].value
    assert isinstance(val, UnaryMinus)


def t_parse_list_literal():
    from ast_nodes import ListLit
    val = parse_src("order = [1, 2, 3]").body[0].value
    assert isinstance(val, ListLit) and len(val.items) == 3


def t_parse_import():
    node = parse_src("import from sounds as s").body[0]
    assert isinstance(node, Import) and node.items[0][1] == "s"


def t_parse_qualified():
    from ast_nodes import Qualified
    val = parse_src("x = s.kick").body[0].value
    assert isinstance(val, Qualified) and val.module == "s" and val.sound == "kick"


def t_parse_call_stmt():
    from ast_nodes import CallStmt
    node = parse_src("void foo(a):\n    x = a\nfoo(1)").body[1]
    assert isinstance(node, CallStmt)


def t_parse_index_expr():
    from ast_nodes import Index
    val = parse_src("x = arr[2]").body[0].value
    assert isinstance(val, Index)


test("Parse simple assignment", t_parse_assign)
test("Parse augmented assignment", t_parse_augassign)
test("Parse for-range loop", t_parse_for_range)
test("Parse for-list loop", t_parse_for_list)
test("Parse while loop", t_parse_while)
test("Parse function definition", t_parse_func_def)
test("Parse return statement", t_parse_return)
test("Parse play statement", t_parse_play)
test("Parse sleep statement", t_parse_sleep)
test("Parse binary op precedence (* binds tighter)", t_parse_binop_precedence)
test("Parse unary minus", t_parse_unary_minus)
test("Parse list literal", t_parse_list_literal)
test("Parse import statement", t_parse_import)
test("Parse qualified sound reference", t_parse_qualified)
test("Parse call statement", t_parse_call_stmt)
test("Parse index expression", t_parse_index_expr)


# =============================================================================
# PHASE 3: SEMANTIC ANALYSIS
# =============================================================================
print(f"\n{BOLD}=== PHASE 3: SEMANTIC ANALYSIS ==={RESET}")


def analyze(src):
    ast = parse_src(src)
    sa = SemanticAnalyzer(BASE)
    sa.analyze(ast)
    return sa


def t_sem_undefined_var():
    expect_error(lambda: analyze("x += 1"), "undefined variable")


def t_sem_undefined_function():
    expect_error(lambda: analyze("foo()"), "undefined function")


def t_sem_return_outside_func():
    expect_error(lambda: analyze("return 1"), "return")


def t_sem_void_return_value():
    expect_error(lambda: analyze("void f(a):\n    return a\nf(1)"), "cannot return")


def t_sem_nonvoid_empty_return():
    expect_error(lambda: analyze("int f(a):\n    return\nf(1)"), "must return")


def t_sem_arg_count_mismatch():
    expect_error(lambda: analyze("void f(a, b):\n    x = a\nf(1)"), "argument")


def t_sem_duplicate_function():
    expect_error(
        lambda: analyze("void f():\n    x = 1\nvoid f():\n    x = 2"),
        "already defined"
    )


def t_sem_call_void_as_value():
    expect_error(lambda: analyze("void f():\n    x = 1\nx = f()"), "void function")


def t_sem_global_volume_ok():
    analyze("volume = 100")  # must not raise


def t_sem_volume_in_func():
    expect_error(lambda: analyze("void f():\n    volume = 50\nf()"), "volume")


test("Undefined variable raises error", t_sem_undefined_var)
test("Undefined function raises error", t_sem_undefined_function)
test("Return outside function raises error", t_sem_return_outside_func)
test("void function returning a value raises error", t_sem_void_return_value)
test("Non-void function empty return raises error", t_sem_nonvoid_empty_return)
test("Argument count mismatch raises error", t_sem_arg_count_mismatch)
test("Duplicate function definition raises error", t_sem_duplicate_function)
test("Calling void function as value raises error", t_sem_call_void_as_value)
test("Global volume statement is valid", t_sem_global_volume_ok)
test("Volume inside function raises error", t_sem_volume_in_func)


# =============================================================================
# PHASE 4: IR GENERATION
# =============================================================================
print(f"\n{BOLD}=== PHASE 4: IR GENERATION ==={RESET}")


def t_ir_assign():
    from ir import IRAssign
    assert isinstance(gen_ir("x = 5").globals[0], IRAssign)


def t_ir_for_range():
    from ir import IRFor
    assert isinstance(gen_ir("for i in range(3):\n    x = i").globals[0], IRFor)


def t_ir_while():
    from ir import IRWhile
    assert isinstance(gen_ir("count = 0\nwhile count < 3:\n    count += 1").globals[1], IRWhile)


def t_ir_function_created():
    ir = gen_ir("void f(a):\n    x = a\nf(1)")
    assert len(ir.functions) == 1 and ir.functions[0].name == "f"


def t_ir_function_return_type():
    """IRFunction.return_type must propagate from FuncDef.ret_type."""
    ir = gen_ir("int add(a):\n    return a\nadd(1)")
    fn = ir.functions[0]
    assert hasattr(fn, "return_type"), "IRFunction missing 'return_type' field"
    assert fn.return_type == "int", f"Expected 'int', got {fn.return_type!r}"


def t_ir_volume_dropped():
    from ir import IRAssign
    for stmt in gen_ir("volume = 100\nx = 1").globals:
        if isinstance(stmt, IRAssign):
            assert stmt.name != "volume", "volume leaked into IR globals"


def t_ir_import_dropped():
    assert len(gen_ir("x = 1").globals) == 1


def t_ir_format_for():
    text = format_ir(gen_ir("for i in range(3):\n    x = i"))
    assert "FOR" in text and "range(3)" in text


def t_ir_format_while():
    text = format_ir(gen_ir("count = 0\nwhile count < 3:\n    count += 1"))
    assert "WHILE" in text


test("IR assign node", t_ir_assign)
test("IR for-range node", t_ir_for_range)
test("IR while node", t_ir_while)
test("IR function generated", t_ir_function_created)
test("IR function return_type matches FuncDef.ret_type", t_ir_function_return_type)
test("volume dropped from IR globals", t_ir_volume_dropped)
test("Import dropped from IR globals", t_ir_import_dropped)
test("format_ir for-range", t_ir_format_for)
test("format_ir while", t_ir_format_while)


# =============================================================================
# PHASE 5: OPTIMIZER
# =============================================================================
print(f"\n{BOLD}=== PHASE 5: OPTIMIZER ==={RESET}")


def optimize(src):
    return Optimizer().optimize(gen_ir(src))


def t_opt_fold_add():
    from ast_nodes import Num
    val = optimize("x = 2 + 3").globals[0].value
    assert isinstance(val, Num) and val.value == 5


def t_opt_fold_mul():
    from ast_nodes import Num
    val = optimize("x = 4 * 5").globals[0].value
    assert isinstance(val, Num) and val.value == 20


def t_opt_fold_unary():
    from ast_nodes import Num
    val = optimize("x = -7").globals[0].value
    assert isinstance(val, Num) and val.value == -7


def t_opt_dead_while():
    from ir import IRWhile
    for stmt in optimize("count = 0\nwhile 0:\n    count += 1").globals:
        assert not isinstance(stmt, IRWhile), "Dead while(0) not removed"


def t_opt_dead_after_return():
    from ir import IRReturn
    fn = optimize("int f(a):\n    return a\n    x = 99\nf(1)").functions[0]
    assert len(fn.body) == 1 and isinstance(fn.body[-1], IRReturn)


def t_opt_div_zero_no_crash():
    from ast_nodes import BinOp
    val = optimize("x = 5 / 0").globals[0].value
    assert isinstance(val, BinOp), "Division by zero should NOT be folded"


test("Constant fold addition 2+3=5", t_opt_fold_add)
test("Constant fold multiplication 4*5=20", t_opt_fold_mul)
test("Constant fold unary minus -7", t_opt_fold_unary)
test("Dead while(0) removed by optimizer", t_opt_dead_while)
test("Dead code after return removed", t_opt_dead_after_return)
test("Division by zero not folded (no crash)", t_opt_div_zero_no_crash)


# =============================================================================
# PHASE 6: NATIVE CODE GENERATION
# =============================================================================
print(f"\n{BOLD}=== PHASE 6: NATIVE CODE GENERATION ==={RESET}")


def t_asm_main_label():
    assert "main:" in gen_asm("x = 5")


def t_asm_intel_syntax():
    assert ".intel_syntax noprefix" in gen_asm("x = 5")


def t_asm_bss_variable():
    assert "var_x:" in gen_asm("x = 5")


def t_asm_for_range_labels():
    asm = gen_asm("for i in range(3):\n    x = i")
    assert "for_" in asm and "endfor_" in asm


def t_asm_while_labels():
    asm = gen_asm("count = 0\nwhile count < 3:\n    count += 1")
    assert "while_" in asm and "endwhile_" in asm


def t_asm_extern_play():
    assert ".extern beatit_play" in gen_asm("x = 5")


def t_asm_extern_sleep():
    assert ".extern beatit_sleep" in gen_asm("x = 5")


def t_asm_list_bss():
    asm = gen_asm("order = [1, 2, 3]\nfor i in order:\n    x = i")
    assert "list_order:" in asm


def t_asm_function_label():
    assert "fn_f:" in gen_asm("void f(a):\n    x = a\nf(1)")


def t_asm_ret_instruction():
    assert "ret" in gen_asm("x = 5")


test("Assembly contains main: label", t_asm_main_label)
test("Assembly uses Intel syntax directive", t_asm_intel_syntax)
test("Assembly has .bss variable entry", t_asm_bss_variable)
test("Assembly for-range loop labels present", t_asm_for_range_labels)
test("Assembly while-loop labels present", t_asm_while_labels)
test("Assembly declares extern beatit_play", t_asm_extern_play)
test("Assembly declares extern beatit_sleep", t_asm_extern_sleep)
test("Assembly list variable in .bss", t_asm_list_bss)
test("Assembly user function has fn_ prefix label", t_asm_function_label)
test("Assembly has ret instruction", t_asm_ret_instruction)


# =============================================================================
# PHASE 7: FULL COMPILE PIPELINE (end-to-end)
# =============================================================================
print(f"\n{BOLD}=== PHASE 7: FULL COMPILE PIPELINE ==={RESET}")

MAIN_BI   = BASE / "main.bi"
BUILD_DIR = BASE / "build"
BUILD_DIR.mkdir(exist_ok=True)


def t_pipeline_all_phases():
    build = compile_pipeline(MAIN_BI)
    assert build.tokens and build.ast and build.ir
    assert build.optimized_ir and build.asm_source


def t_pipeline_produces_exe():
    out, _ = compile_file(MAIN_BI, str(BUILD_DIR / "main.exe"))
    assert out.is_file() and out.suffix == ".exe"


def t_pipeline_artifacts():
    out_exe = BUILD_DIR / "main.exe"
    art = BUILD_DIR / "main_artifacts"
    compile_file(MAIN_BI, str(out_exe))
    assert (art / "main.ir").is_file()
    assert (art / "main.optimized.ir").is_file()
    assert (art / "main.s").is_file()


def t_pipeline_sound_folder_copied():
    compile_file(MAIN_BI, str(BUILD_DIR / "main.exe"))
    assert (BUILD_DIR / "sounds").is_dir(), "sounds/ not copied next to exe"


test("Pipeline runs all phases without error", t_pipeline_all_phases)
test("Pipeline produces a .exe file", t_pipeline_produces_exe)
test("Phase artifacts (.ir, .optimized.ir, .s) are created", t_pipeline_artifacts)
test("Sound folder copied next to executable", t_pipeline_sound_folder_copied)


# =============================================================================
# DECOMPILER: REVERSE ENGINEERING
# =============================================================================
print(f"\n{BOLD}=== DECOMPILER: REVERSE ENGINEERING ==={RESET}")

EXE_FILE = BUILD_DIR / "main.exe"


def t_decompile_produces_bi():
    out_bi = BUILD_DIR / "test_dc.bi"
    result = decompile_file(EXE_FILE, str(out_bi))
    assert result.is_file() and result.suffix == ".bi"


def t_decompile_mz_check():
    tmp = Path(tempfile.mktemp(suffix=".exe"))
    tmp.write_bytes(b"NOTANEXE")
    try:
        expect_error(lambda: decompile_file(tmp), "PE executable")
    finally:
        tmp.unlink(missing_ok=True)


def t_decompile_extract_sounds():
    data = b"sounds/kick.wav\x00sounds/snare.wav\x00"
    sounds = extract_sound_strings(data)
    assert "sounds/kick.wav" in sounds
    assert "sounds/snare.wav" in sounds


def t_decompile_has_import():
    out_bi = BUILD_DIR / "test_dc.bi"
    decompile_file(EXE_FILE, str(out_bi))
    assert "import from" in out_bi.read_text(encoding="utf-8")


def t_decompile_has_for_loop():
    out_bi = BUILD_DIR / "test_dc.bi"
    decompile_file(EXE_FILE, str(out_bi))
    assert "for " in out_bi.read_text(encoding="utf-8")


def t_decompile_has_play():
    out_bi = BUILD_DIR / "test_dc.bi"
    decompile_file(EXE_FILE, str(out_bi))
    assert "play(" in out_bi.read_text(encoding="utf-8")


def t_decompile_nonexistent():
    """decompile_file raises FileNotFoundError for a missing file (matches main.py handler)."""
    try:
        decompile_file(BUILD_DIR / "nonexistent.exe")
        raise AssertionError("Expected FileNotFoundError but no error was raised")
    except FileNotFoundError:
        pass  # correct behaviour


test("Decompile produces .bi output file", t_decompile_produces_bi)
test("Decompile rejects non-PE file (MZ header check)", t_decompile_mz_check)
test("extract_sound_strings finds .wav paths in binary", t_decompile_extract_sounds)
test("Decompiled .bi has import statement", t_decompile_has_import)
test("Decompiled .bi has for loop", t_decompile_has_for_loop)
test("Decompiled .bi has play() call", t_decompile_has_play)
test("Decompile of nonexistent file raises error", t_decompile_nonexistent)


# =============================================================================
# SUMMARY
# =============================================================================
total = passed + failed
print(f"\n{'='*60}")
print(f"  {BOLD}RESULTS: {passed}/{total} passed,  {failed} failed{RESET}")
print(f"{'='*60}")

if errors:
    print(f"\n{RED}Failed tests:{RESET}")
    for name, msg, tb in errors:
        print(f"\n  {RED}FAIL{RESET} {name}")
        print(f"       {msg}")
        tb_lines = [l.strip() for l in tb.strip().splitlines()
                    if l.strip() and not l.strip().startswith("Traceback")]
        if tb_lines:
            print(f"       {tb_lines[-2] if len(tb_lines) >= 2 else tb_lines[-1]}")

sys.exit(0 if failed == 0 else 1)
