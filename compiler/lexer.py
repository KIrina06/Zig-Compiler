import ply.lex as lex


class ZigLexerError(Exception):
    pass


reserved = {
    # declarations
    "const": "CONST",
    "var": "VAR",
    "fn": "FN",
    "struct": "STRUCT",
    "enum": "ENUM",
    "union": "UNION",
    "pub": "PUB",
    "extern": "EXTERN",
    "comptime": "COMPTIME",
    "inline": "INLINE",

    # control flow
    "return": "RETURN",
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "break": "BREAK",
    "continue": "CONTINUE",
    "switch": "SWITCH",

    # literals / builtins-ish
    "true": "TRUE",
    "false": "FALSE",
    "null": "NULL",
    "undefined": "UNDEFINED",

    # common Zig primitive types
    "void": "TYPE_VOID",
    "bool": "TYPE_BOOL",
    "usize": "TYPE_USIZE",
    "isize": "TYPE_ISIZE",
    "u8": "TYPE_U8",
    "u16": "TYPE_U16",
    "u32": "TYPE_U32",
    "u64": "TYPE_U64",
    "i8": "TYPE_I8",
    "i16": "TYPE_I16",
    "i32": "TYPE_I32",
    "i64": "TYPE_I64",
}


tokens = [
    # identifiers and literals
    "IDENT",
    "BUILTIN_IDENT",
    "INT",
    "STRING",
    "CHAR",

    # arithmetic
    "PLUS",
    "MINUS",
    "STAR",
    "SLASH",
    "PERCENT",

    # assignment / compound assignment
    "EQ",
    "PLUS_EQ",
    "MINUS_EQ",
    "STAR_EQ",
    "SLASH_EQ",
    "PERCENT_EQ",

    # comparison
    "EQEQ",
    "NE",
    "LT",
    "LE",
    "GT",
    "GE",

    # boolean / bit ops
    "BANG",
    "ANDAND",
    "OROR",
    "AMP",
    "PIPE",
    "CARET",
    "TILDE",

    # punctuation
    "LPAREN",
    "RPAREN",
    "LBRACE",
    "RBRACE",
    "LBRACKET",
    "RBRACKET",
    "COLON",
    "SEMICOLON",
    "COMMA",
    "DOT",
    "DOTDOT",
    "QUESTION",

    # arrows / fat arrows
    "ARROW",
    "FATARROW",
] + list(reserved.values())


# Important: longer regex rules must appear before shorter overlapping ones.
t_ARROW = r"->"
t_FATARROW = r"=>"

t_PLUS_EQ = r"\+="
t_MINUS_EQ = r"-="
t_STAR_EQ = r"\*="
t_SLASH_EQ = r"/="
t_PERCENT_EQ = r"%="

t_EQEQ = r"=="
t_NE = r"!="
t_LE = r"<="
t_GE = r">="

t_ANDAND = r"&&"
t_OROR = r"\|\|"

t_DOTDOT = r"\.\."

t_PLUS = r"\+"
t_MINUS = r"-"
t_STAR = r"\*"
t_SLASH = r"/"
t_PERCENT = r"%"

t_EQ = r"="
t_LT = r"<"
t_GT = r">"

t_BANG = r"!"
t_AMP = r"&"
t_PIPE = r"\|"
t_CARET = r"\^"
t_TILDE = r"~"

t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_LBRACKET = r"\["
t_RBRACKET = r"\]"

t_COLON = r":"
t_SEMICOLON = r";"
t_COMMA = r","
t_DOT = r"\."
t_QUESTION = r"\?"


t_ignore = " \t\r"


def t_LINE_COMMENT(t):
    r"//[^\n]*"
    pass


def t_BLOCK_COMMENT(t):
    r"/\*[\s\S]*?\*/"
    t.lexer.lineno += t.value.count("\n")
    pass


def t_STRING(t):
    r'"([^"\\]|\\.)*"'
    return t


def t_CHAR(t):
    r"'([^'\\]|\\.)'"
    return t


def t_BUILTIN_IDENT(t):
    r"@[A-Za-z_][A-Za-z0-9_]*"
    return t


def t_INT(t):
    r"0b[01_]+|0o[0-7_]+|0x[0-9a-fA-F_]+|[0-9][0-9_]*"
    raw = t.value.replace("_", "")
    if raw.startswith("0b"):
        t.value = int(raw[2:], 2)
    elif raw.startswith("0o"):
        t.value = int(raw[2:], 8)
    elif raw.startswith("0x"):
        t.value = int(raw[2:], 16)
    else:
        t.value = int(raw, 10)
    return t


def t_IDENT(t):
    r"[A-Za-z_][A-Za-z0-9_]*"
    t.type = reserved.get(t.value, "IDENT")
    return t


def t_newline(t):
    r"\n+"
    t.lexer.lineno += len(t.value)


def t_error(t):
    raise ZigLexerError(
        f"Unexpected character {t.value[0]!r} at line {t.lexer.lineno}"
    )


def build_lexer(**kwargs):
    return lex.lex(**kwargs)


def tokenize(source: str):
    lexer = build_lexer()
    lexer.input(source)
    return list(lexer)


def token_types(source: str):
    return [tok.type for tok in tokenize(source)]


def token_values(source: str):
    return [(tok.type, tok.value) for tok in tokenize(source)]


if __name__ == "__main__":
    code = r'''
    const std = @import("std");

    fn fib(n: u32) u32 {
        if (n <= 1) {
            return n;
        }
        return fib(n - 1) + fib(n - 2);
    }
    '''

    for token in tokenize(code):
        print(token)