"""Command-line driver for running, compiling, and decompiling Beat It code."""
import argparse
import sys
from pathlib import Path
from pprint import pprint

from errors import BeatItError


def main(argv=None):
    ap = argparse.ArgumentParser(description="Beat It audio programming language")
    ap.add_argument("file", help="command: compile or decompile")
    ap.add_argument("command_file", nargs="?", help=argparse.SUPPRESS)
    ap.add_argument("--tokens", action="store_true", help="print tokens and stop")
    ap.add_argument("--ast", action="store_true", help="print the syntax tree and stop")
    ap.add_argument("--ir", action="store_true", help="print phase-4 intermediate code and stop")
    ap.add_argument("--optimized-ir", action="store_true", help="print optimized intermediate code and stop")
    ap.add_argument("--asm", action="store_true", help="print generated assembly after compilation")
    ap.add_argument("-o", "--output", help="output .exe or .bi path for compile/decompile")
    ap.add_argument("--emit-dir", help="folder for generated .ir, .optimized.ir, .c, and .s files")
    args = ap.parse_args(argv)

    try:
        if args.file == "compile":
            if not args.command_file:
                ap.error("compile needs a source file: compile program.bi [-o program.exe]")
            from compiler import compile_file, compile_pipeline
            from ir import format_ir
            build = compile_pipeline(Path(args.command_file))
            if args.tokens:
                for token in build.tokens: print(token)
                return
            if args.ast:
                pprint(build.ast, width=100)
                return
            if args.ir:
                print(format_ir(build.ir))
                return
            if args.optimized_ir:
                print(format_ir(build.optimized_ir))
                return
            output, artifacts = compile_file(Path(args.command_file), args.output, args.emit_dir)
            print(f"Created native executable: {output}")
            print(f"Phase artifacts: {artifacts}")
            if args.asm:
                print((artifacts / f"{output.stem}.s").read_text(encoding="utf-8"))
            return
        if args.file == "decompile":
            if not args.command_file:
                ap.error("decompile needs an executable: decompile program.exe [-o restored.bi]")
            from decompiler import decompile_file
            output = decompile_file(Path(args.command_file), args.output)
            print(f"Restored source: {output}")
            return
        ap.error("use 'compile program.bi' or 'decompile program.exe'")
    except BeatItError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: input file not found", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
