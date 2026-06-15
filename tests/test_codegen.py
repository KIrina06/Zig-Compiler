from compiler.parser import parse
from compiler.semantic import analyze
from compiler.codegen import generate_llvm_ir


def compile_to_ir(src: str) -> str:
    program = parse(src)
    analyze(program)
    return generate_llvm_ir(program)


def test_codegen_generates_fibonacci_ir():
    src = """
    fn fib(n: i32) i32 {
        if (n <= 1) {
            return n;
        }

        return fib(n - 1) + fib(n - 2);
    }
    """

    llvm_ir = compile_to_ir(src)

    assert 'define i32 @"fib"' in llvm_ir
    assert "icmp sle" in llvm_ir
    assert "call i32 @\"fib\"" in llvm_ir
    assert "ret i32" in llvm_ir


def test_codegen_generates_main_with_print():
    src = """
    const std = @import("std");

    fn main() void {
        std.debug.print("answer = {}\\n", .{42});
    }
    """

    llvm_ir = compile_to_ir(src)

    assert 'declare i32 @"printf"' in llvm_ir
    assert 'define void @"main"' in llvm_ir
    assert "printf_call" in llvm_ir
    assert "answer = %d" in llvm_ir


def test_codegen_generates_arithmetic():
    src = """
    fn calc() i32 {
        const x: i32 = 10;
        const y: i32 = 20;
        return x + y * 2;
    }
    """

    llvm_ir = compile_to_ir(src)

    assert 'define i32 @"calc"' in llvm_ir
    assert "mul" in llvm_ir
    assert "add" in llvm_ir

def test_codegen_generates_while_loop():
    src = """
    fn sum_to(n: i32) i32 {
        var i: i32 = 0;
        var sum: i32 = 0;

        while (i < n) {
            sum += i;
            i += 1;
        }

        return sum;
    }
    """

    llvm_ir = compile_to_ir(src)

    assert "while.cond" in llvm_ir
    assert "while.body" in llvm_ir
    assert "while.end" in llvm_ir
    assert "icmp slt" in llvm_ir


def test_codegen_generates_for_range_loop():
    src = """
    fn sum_to(n: i32) i32 {
        var sum: i32 = 0;

        for (0..n) |i| {
            sum += i;
        }

        return sum;
    }
    """

    llvm_ir = compile_to_ir(src)

    assert "for.cond" in llvm_ir
    assert "for.body" in llvm_ir
    assert "for.end" in llvm_ir


def test_codegen_generates_array_indexing():
    src = """
    fn main() i32 {
        var a: [3]i32;
        a[0] = 10;
        a[1] = 20;
        a[2] = a[0] + a[1];
        return a[2];
    }
    """

    llvm_ir = compile_to_ir(src)

    assert "[3 x i32]" in llvm_ir
    assert "getelementptr" in llvm_ir
    assert "ret i32" in llvm_ir


def test_codegen_generates_simple_array_sort_like_code():
    src = """
    fn main() i32 {
        var a: [3]i32;

        a[0] = 3;
        a[1] = 1;
        a[2] = 2;

        if (a[0] > a[1]) {
            var tmp: i32 = a[0];
            a[0] = a[1];
            a[1] = tmp;
        }

        return a[0];
    }
    """

    llvm_ir = compile_to_ir(src)

    assert "[3 x i32]" in llvm_ir
    assert "icmp sgt" in llvm_ir
    assert "getelementptr" in llvm_ir

def test_codegen_generates_struct_field_assignment():
    src = """
    const Node = struct {
        value: i32,
    };

    fn main() i32 {
        var node: Node = undefined;
        node.value = 42;
        return node.value;
    }
    """

    llvm_ir = compile_to_ir(src)

    assert '%"Node" = type {i32}' in llvm_ir
    assert "getelementptr" in llvm_ir
    assert "ret i32" in llvm_ir


def test_codegen_generates_struct_with_pointer_fields():
    src = """
    const Node = struct {
        value: i32,
        next: ?*Node,
        prev: ?*Node,
    };

    fn main() i32 {
        var node: Node = undefined;
        node.value = 10;
        node.next = null;
        node.prev = null;
        return node.value;
    }
    """

    llvm_ir = compile_to_ir(src)

    assert '%"Node" = type {i32, %"Node"*, %"Node"*}' in llvm_ir
    assert "null" in llvm_ir
    assert "getelementptr" in llvm_ir