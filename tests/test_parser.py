import pytest

from compiler.parser import ZigParserError, parse
from compiler import ast


def test_parse_fibonacci_function():
    src = """
    fn fib(n: u32) u32 {
        if (n <= 1) {
            return n;
        }
        return fib(n - 1) + fib(n - 2);
    }
    """

    program = parse(src)

    assert isinstance(program, ast.Program)
    assert len(program.declarations) == 1

    fib = program.declarations[0]
    assert isinstance(fib, ast.FnDecl)
    assert fib.name == "fib"
    assert len(fib.params) == 1
    assert fib.params[0].name == "n"
    assert isinstance(fib.return_type, ast.NamedType)
    assert fib.return_type.name == "u32"
    assert len(fib.body.statements) == 2
    assert isinstance(fib.body.statements[0], ast.IfStmt)
    assert isinstance(fib.body.statements[1], ast.ReturnStmt)


def test_parse_print_call_with_field_access():
    src = r'''
    const std = @import("std");

    fn main() void {
        std.debug.print("answer = {}
", 42);
    }
    '''

    program = parse(src)

    assert len(program.declarations) == 2
    main_fn = program.declarations[1]
    stmt = main_fn.body.statements[0]

    assert isinstance(stmt, ast.ExprStmt)
    assert isinstance(stmt.expr, ast.CallExpr)

    call = stmt.expr
    assert len(call.args) == 2
    assert isinstance(call.callee, ast.FieldAccess)
    assert call.callee.field == "print"

    debug_access = call.callee.object
    assert isinstance(debug_access, ast.FieldAccess)
    assert debug_access.field == "debug"

    std_ident = debug_access.object
    assert isinstance(std_ident, ast.Identifier)
    assert std_ident.name == "std"


def test_parse_struct_for_doubly_linked_list_node():
    src = """
    const Node = struct {
        value: i32,
        next: ?*Node,
        prev: ?*Node,
    };
    """

    program = parse(src)
    decl = program.declarations[0]

    assert isinstance(decl, ast.VarDecl)
    assert decl.kind == "const"
    assert decl.name == "Node"
    assert isinstance(decl.value, ast.StructDecl)
    assert len(decl.value.fields) == 3
    assert decl.value.fields[0].name == "value"
    assert decl.value.fields[1].name == "next"
    assert decl.value.fields[2].name == "prev"

    next_type = decl.value.fields[1].type_name
    assert isinstance(next_type, ast.OptionalType)
    assert isinstance(next_type.inner, ast.PointerType)
    assert isinstance(next_type.inner.inner, ast.NamedType)
    assert next_type.inner.inner.name == "Node"


def test_parse_array_indexing_and_assignment_for_sorting():
    src = """
    fn swap(a: []i32, i: usize, j: usize) void {
        const tmp = a[i];
        a[i] = a[j];
        a[j] = tmp;
    }
    """

    program = parse(src)
    fn = program.declarations[0]

    assert isinstance(fn, ast.FnDecl)
    assert fn.name == "swap"
    assert len(fn.params) == 3
    assert isinstance(fn.params[0].type_name, ast.SliceType)

    assert isinstance(fn.body.statements[0], ast.VarDecl)
    assert isinstance(fn.body.statements[1], ast.AssignStmt)
    assert isinstance(fn.body.statements[1].target, ast.IndexAccess)
    assert isinstance(fn.body.statements[2], ast.AssignStmt)


def test_parse_while_loop_for_bfs_style_code():
    src = """
    fn bfs(queue: []usize, visited: []bool, tail: usize) void {
        var head: usize = 0;
        while (head < tail) {
            const v = queue[head];
            head += 1;
            visited[v] = true;
        }
    }
    """

    program = parse(src)
    fn = program.declarations[0]

    assert isinstance(fn.body.statements[0], ast.VarDecl)
    assert isinstance(fn.body.statements[1], ast.WhileStmt)

    while_stmt = fn.body.statements[1]
    assert isinstance(while_stmt.condition, ast.BinaryOp)
    assert while_stmt.condition.op == "<"
    assert len(while_stmt.body.statements) == 3
    assert isinstance(while_stmt.body.statements[1], ast.AssignStmt)
    assert while_stmt.body.statements[1].op == "+="


def test_parse_for_range_loop():
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
    fn = program.declarations[0]
    for_stmt = fn.body.statements[1]

    assert isinstance(for_stmt, ast.ForStmt)
    assert for_stmt.capture == "i"
    assert isinstance(for_stmt.iterable, ast.RangeExpr)


def test_parse_field_access_assignment_for_linked_list():
    src = """
    fn connect(a: *Node, b: *Node) void {
        a.next = b;
        b.prev = a;
    }
    """

    program = parse(src)
    fn = program.declarations[0]

    first = fn.body.statements[0]
    second = fn.body.statements[1]

    assert isinstance(first, ast.AssignStmt)
    assert isinstance(first.target, ast.FieldAccess)
    assert first.target.field == "next"

    assert isinstance(second, ast.AssignStmt)
    assert isinstance(second.target, ast.FieldAccess)
    assert second.target.field == "prev"


def test_parse_error_on_invalid_syntax():
    with pytest.raises(ZigParserError):
        parse("fn broken( void {")
