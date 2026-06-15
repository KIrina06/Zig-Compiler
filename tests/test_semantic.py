import pytest

from compiler.parser import parse
from compiler.semantic import SemanticAnalyzer, SemanticError, analyze


def test_semantic_accepts_fibonacci_program():
    src = """
    const std = @import("std");

    fn fib(n: u32) u32 {
        if (n <= 1) {
            return n;
        }

        return fib(n - 1) + fib(n - 2);
    }

    fn main() void {
        std.debug.print("fib = {}\\n", .{fib(10)});
    }
    """

    program = parse(src)
    scope = analyze(program)

    assert scope.resolve("fib") is not None
    assert scope.resolve("main") is not None


def test_semantic_rejects_undeclared_variable():
    src = """
    fn main() void {
        x = 10;
    }
    """

    program = parse(src)

    with pytest.raises(SemanticError, match="undeclared identifier"):
        analyze(program)


def test_semantic_rejects_redeclaration_in_same_scope():
    src = """
    fn main() void {
        var x: i32 = 1;
        var x: i32 = 2;
    }
    """

    program = parse(src)

    with pytest.raises(SemanticError, match="Redeclaration"):
        analyze(program)


def test_semantic_rejects_assignment_to_const():
    src = """
    fn main() void {
        const x: i32 = 1;
        x = 2;
    }
    """

    program = parse(src)

    with pytest.raises(SemanticError, match="Cannot assign to const"):
        analyze(program)


def test_semantic_accepts_struct_and_field_access():
    src = """
    const Node = struct {
        value: i32,
        next: ?*Node,
    };

    fn main() void {
        var node: Node = undefined;
        node.value = 10;
    }
    """

    program = parse(src)
    analyze(program)


def test_semantic_rejects_duplicate_struct_field():
    src = """
    const Bad = struct {
        value: i32,
        value: i32,
    };
    """

    program = parse(src)

    with pytest.raises(SemanticError, match="Duplicate struct field"):
        analyze(program)


def test_semantic_accepts_for_loop_capture():
    src = """
    fn sum_to(n: usize) usize {
        var sum: usize = 0;

        for (0..n) |i| {
            sum += i;
        }

        return sum;
    }
    """

    program = parse(src)
    analyze(program)


def test_global_scope_contains_builtin_types():
    analyzer = SemanticAnalyzer()
    scope = analyzer.analyze(parse("fn main() void {}"))

    assert scope.resolve("i32") is not None
    assert scope.resolve("usize") is not None
    assert scope.resolve("void") is not None