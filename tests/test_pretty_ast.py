from compiler.parser import parse
from compiler.pretty_ast import format_ast


def test_format_ast_contains_main_nodes():
    src = """
    fn main() void {
        std.debug.print("answer = {}\n", 42);
    }
    """

    tree = format_ast(parse(src))

    assert "Program" in tree
    assert "FnDecl" in tree
    assert "CallExpr" in tree
    assert "FieldAccess" in tree
    assert "StringLiteral" in tree
    assert "IntLiteral" in tree