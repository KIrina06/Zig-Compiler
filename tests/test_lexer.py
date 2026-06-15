import pytest

from compiler.lexer import ZigLexerError, token_types, token_values


def test_const_and_var_declarations():
    src = """
    const x: i32 = 10;
    var y: usize = x + 20;
    """

    assert token_types(src) == [
        "CONST", "IDENT", "COLON", "TYPE_I32", "EQ", "INT", "SEMICOLON",
        "VAR", "IDENT", "COLON", "TYPE_USIZE", "EQ", "IDENT", "PLUS", "INT", "SEMICOLON",
    ]


def test_function_fibonacci_tokens():
    src = """
    fn fib(n: u32) u32 {
        if (n <= 1) {
            return n;
        }
        return fib(n - 1) + fib(n - 2);
    }
    """

    assert token_types(src) == [
        "FN", "IDENT", "LPAREN", "IDENT", "COLON", "TYPE_U32", "RPAREN", "TYPE_U32",
        "LBRACE",
        "IF", "LPAREN", "IDENT", "LE", "INT", "RPAREN",
        "LBRACE", "RETURN", "IDENT", "SEMICOLON", "RBRACE",
        "RETURN", "IDENT", "LPAREN", "IDENT", "MINUS", "INT", "RPAREN",
        "PLUS",
        "IDENT", "LPAREN", "IDENT", "MINUS", "INT", "RPAREN", "SEMICOLON",
        "RBRACE",
    ]


def test_struct_for_linked_list_node():
    src = """
    const Node = struct {
        value: i32,
        next: ?*Node,
        prev: ?*Node,
    };
    """

    assert token_types(src) == [
        "CONST", "IDENT", "EQ", "STRUCT", "LBRACE",
        "IDENT", "COLON", "TYPE_I32", "COMMA",
        "IDENT", "COLON", "QUESTION", "STAR", "IDENT", "COMMA",
        "IDENT", "COLON", "QUESTION", "STAR", "IDENT", "COMMA",
        "RBRACE", "SEMICOLON",
    ]


def test_arrays_and_indexing_for_sorting():
    src = """
    fn swap(a: []i32, i: usize, j: usize) void {
        const tmp = a[i];
        a[i] = a[j];
        a[j] = tmp;
    }
    """

    assert token_types(src) == [
        "FN", "IDENT", "LPAREN",
        "IDENT", "COLON", "LBRACKET", "RBRACKET", "TYPE_I32", "COMMA",
        "IDENT", "COLON", "TYPE_USIZE", "COMMA",
        "IDENT", "COLON", "TYPE_USIZE", "RPAREN", "TYPE_VOID",
        "LBRACE",
        "CONST", "IDENT", "EQ", "IDENT", "LBRACKET", "IDENT", "RBRACKET", "SEMICOLON",
        "IDENT", "LBRACKET", "IDENT", "RBRACKET", "EQ", "IDENT", "LBRACKET", "IDENT", "RBRACKET", "SEMICOLON",
        "IDENT", "LBRACKET", "IDENT", "RBRACKET", "EQ", "IDENT", "SEMICOLON",
        "RBRACE",
    ]


def test_while_loop_for_bfs_or_dfs_style_code():
    src = """
    while (head < tail) {
        const v = queue[head];
        head += 1;
        visited[v] = true;
    }
    """

    assert token_types(src) == [
        "WHILE", "LPAREN", "IDENT", "LT", "IDENT", "RPAREN",
        "LBRACE",
        "CONST", "IDENT", "EQ", "IDENT", "LBRACKET", "IDENT", "RBRACKET", "SEMICOLON",
        "IDENT", "PLUS_EQ", "INT", "SEMICOLON",
        "IDENT", "LBRACKET", "IDENT", "RBRACKET", "EQ", "TRUE", "SEMICOLON",
        "RBRACE",
    ]


def test_for_loop_range_tokens():
    src = """
    for (0..n) |i| {
        sum += i;
    }
    """

    assert token_types(src) == [
        "FOR", "LPAREN", "INT", "DOTDOT", "IDENT", "RPAREN",
        "PIPE", "IDENT", "PIPE",
        "LBRACE",
        "IDENT", "PLUS_EQ", "IDENT", "SEMICOLON",
        "RBRACE",
    ]


def test_builtin_import_and_string_literal():
    src = 'const std = @import("std");'

    assert token_values(src) == [
        ("CONST", "const"),
        ("IDENT", "std"),
        ("EQ", "="),
        ("BUILTIN_IDENT", "@import"),
        ("LPAREN", "("),
        ("STRING", '"std"'),
        ("RPAREN", ")"),
        ("SEMICOLON", ";"),
    ]


def test_integer_literals():
    src = "0 123 1_000 0b1010 0o17 0xff"

    assert token_values(src) == [
        ("INT", 0),
        ("INT", 123),
        ("INT", 1000),
        ("INT", 10),
        ("INT", 15),
        ("INT", 255),
    ]


def test_comments_are_ignored():
    src = """
    const x: i32 = 1; // line comment
    /* block
       comment */
    const y: i32 = 2;
    """

    assert token_types(src) == [
        "CONST", "IDENT", "COLON", "TYPE_I32", "EQ", "INT", "SEMICOLON",
        "CONST", "IDENT", "COLON", "TYPE_I32", "EQ", "INT", "SEMICOLON",
    ]


def test_unexpected_character_raises_error():
    with pytest.raises(ZigLexerError):
        token_types("const x = $;")
