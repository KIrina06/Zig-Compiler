import argparse
import subprocess
from pathlib import Path

from compiler.parser import ZigParserError, parse
from compiler.lexer import ZigLexerError
from compiler.semantic import SemanticError, analyze
from compiler.codegen import CodegenError, generate_llvm_ir
from compiler.pretty_ast import format_ast, format_ast_json, format_ast_dot


def run_command(command: list[str]) -> int:
    print("$ " + " ".join(command))
    completed = subprocess.run(command)
    return completed.returncode


def main() -> int:
    arg_parser = argparse.ArgumentParser(
        prog="zig-python-compiler",
        description="Partial Zig compiler frontend",
    )

    arg_parser.add_argument("source_file")

    arg_parser.add_argument(
        "-o",
        "--output",
        help="Output file path",
    )

    arg_parser.add_argument(
        "--format",
        choices=["tree", "json", "dot", "llvm", "exe"],
        default="tree",
    )

    arg_parser.add_argument(
        "--run",
        action="store_true",
        help="Run generated executable. Works only with --format exe",
    )

    arg_parser.add_argument(
        "--max-leaf-length",
        type=int,
        default=80,
    )

    args = arg_parser.parse_args()
    source_path = Path(args.source_file)

    if not source_path.exists():
        print(f"Error: file not found: {source_path}")
        return 1

    try:
        source = source_path.read_text(encoding="utf-8")
        program = parse(source)

        if args.format == "tree":
            result = format_ast(program, max_leaf_length=args.max_leaf_length)

        elif args.format == "json":
            result = format_ast_json(program)

        elif args.format == "dot":
            result = format_ast_dot(program)

        elif args.format == "llvm":
            analyze(program)
            result = generate_llvm_ir(program)

        elif args.format == "exe":
            analyze(program)
            llvm_ir = generate_llvm_ir(program)

            build_dir = Path("build")
            build_dir.mkdir(exist_ok=True)

            ll_path = build_dir / f"{source_path.stem}.ll"

            if args.output:
                exe_path = Path(args.output)
            else:
                exe_path = build_dir / f"{source_path.stem}.exe"

            ll_path.write_text(llvm_ir, encoding="utf-8")

            code = run_command([
                "clang",
                str(ll_path),
                "-o",
                str(exe_path),
            ])

            if code != 0:
                print("Error: clang failed")
                return code

            print(f"Executable written to: {exe_path}")

            if args.run:
                return run_command([str(exe_path)])

            return 0

        else:
            raise RuntimeError("unreachable")

    except UnicodeDecodeError:
        print(f"Error: cannot read file as UTF-8: {source_path}")
        return 1

    except ZigLexerError as exc:
        print(f"Lexer error: {exc}")
        return 1

    except ZigParserError as exc:
        print(f"Parser error: {exc}")
        return 1

    except SemanticError as exc:
        print(f"Semantic error: {exc}")
        return 1

    except CodegenError as exc:
        print(f"Codegen error: {exc}")
        return 1

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result + "\n", encoding="utf-8")
        print(f"Written to: {output_path}")
    else:
        print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())