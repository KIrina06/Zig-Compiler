import ply.yacc as yacc

from compiler.lexer import tokens, build_lexer
from compiler import ast


class ZigParserError(Exception):
    pass


precedence = (
    ("left", "OROR"),
    ("left", "ANDAND"),
    ("left", "EQEQ", "NE"),
    ("left", "LT", "LE", "GT", "GE"),
    ("left", "PLUS", "MINUS"),
    ("left", "STAR", "SLASH", "PERCENT"),
    ("right", "BANG", "UMINUS", "AMP", "QUESTION"),
    ("left", "DOT", "LBRACKET", "LPAREN"),
)


# =========================
# PROGRAM
# =========================

def p_program(p):
    """program : declarations_opt"""
    p[0] = ast.Program(p[1])


def p_declarations_opt(p):
    """declarations_opt : declarations
                        | empty"""
    p[0] = p[1] or []


def p_declarations(p):
    """declarations : declarations declaration
                    | declaration"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]


def p_declaration(p):
    """declaration : var_decl SEMICOLON
                   | fn_decl"""
    p[0] = p[1]


# =========================
# VARIABLES
# =========================

def p_var_decl(p):
    """var_decl : CONST IDENT type_annotation_opt EQ expression
                | VAR IDENT type_annotation_opt EQ expression
                | VAR IDENT type_annotation"""
    kind = p[1]
    name = p[2]
    type_name = p[3]
    value = p[5] if len(p) == 6 else None
    p[0] = ast.VarDecl(kind, name, type_name, value)


def p_type_annotation_opt(p):
    """type_annotation_opt : type_annotation
                           | empty"""
    p[0] = p[1]


def p_type_annotation(p):
    """type_annotation : COLON type_expr"""
    p[0] = p[2]


# =========================
# FUNCTIONS
# =========================

def p_fn_decl(p):
    """fn_decl : FN IDENT LPAREN params_opt RPAREN return_type_opt block"""
    p[0] = ast.FnDecl(
        name=p[2],
        params=p[4],
        return_type=p[6],
        body=p[7],
    )


def p_params_opt(p):
    """params_opt : params
                  | empty"""
    p[0] = p[1] or []


def p_params(p):
    """params : params COMMA param
              | param"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


def p_param(p):
    """param : IDENT COLON type_expr"""
    p[0] = ast.Param(p[1], p[3])


def p_return_type_opt(p):
    """return_type_opt : type_expr
                       | empty"""
    p[0] = p[1]


# =========================
# TYPES
# =========================

def p_type_expr_named(p):
    """type_expr : IDENT
                 | TYPE_VOID
                 | TYPE_BOOL
                 | TYPE_USIZE
                 | TYPE_ISIZE
                 | TYPE_U8
                 | TYPE_U16
                 | TYPE_U32
                 | TYPE_U64
                 | TYPE_I8
                 | TYPE_I16
                 | TYPE_I32
                 | TYPE_I64"""
    p[0] = ast.NamedType(p[1])


def p_type_expr_struct(p):
    """type_expr : STRUCT LBRACE struct_fields_opt RBRACE"""
    p[0] = ast.StructDecl(p[3])


def p_struct_fields_opt(p):
    """struct_fields_opt : struct_fields
                         | empty"""
    p[0] = p[1] or []


def p_struct_fields(p):
    """struct_fields : struct_fields struct_field
                     | struct_field"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]


def p_struct_field(p):
    """struct_field : IDENT COLON type_expr COMMA
                    | IDENT COLON type_expr"""
    p[0] = ast.StructField(p[1], p[3])


def p_type_expr_optional(p):
    """type_expr : QUESTION type_expr"""
    p[0] = ast.OptionalType(p[2])


def p_type_expr_pointer(p):
    """type_expr : STAR type_expr"""
    p[0] = ast.PointerType(p[2])


def p_type_expr_slice(p):
    """type_expr : LBRACKET RBRACKET type_expr"""
    p[0] = ast.SliceType(p[3])


def p_type_expr_array(p):
    """type_expr : LBRACKET expression RBRACKET type_expr"""
    p[0] = ast.ArrayType(p[2], p[4])


# =========================
# BLOCKS / STATEMENTS
# =========================

def p_block(p):
    """block : LBRACE statements_opt RBRACE"""
    p[0] = ast.Block(p[2])


def p_statements_opt(p):
    """statements_opt : statements
                      | empty"""
    p[0] = p[1] or []


def p_statements(p):
    """statements : statements statement
                  | statement"""
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]


def p_statement(p):
    """statement : var_decl SEMICOLON
                 | return_stmt SEMICOLON
                 | break_stmt SEMICOLON
                 | continue_stmt SEMICOLON
                 | assignment SEMICOLON
                 | expr_stmt SEMICOLON
                 | if_stmt
                 | while_stmt
                 | for_stmt"""
    p[0] = p[1]


def p_return_stmt(p):
    """return_stmt : RETURN expression
                   | RETURN"""
    p[0] = ast.ReturnStmt(p[2] if len(p) == 3 else None)


def p_break_stmt(p):
    """break_stmt : BREAK"""
    p[0] = ast.BreakStmt()


def p_continue_stmt(p):
    """continue_stmt : CONTINUE"""
    p[0] = ast.ContinueStmt()


def p_if_stmt(p):
    """if_stmt : IF LPAREN expression RPAREN block else_opt"""
    p[0] = ast.IfStmt(p[3], p[5], p[6])


def p_else_opt(p):
    """else_opt : ELSE block
                | empty"""
    p[0] = p[2] if len(p) == 3 else None


def p_while_stmt(p):
    """while_stmt : WHILE LPAREN expression RPAREN block"""
    p[0] = ast.WhileStmt(p[3], p[5])


def p_for_stmt(p):
    """for_stmt : FOR LPAREN expression RPAREN PIPE IDENT PIPE block"""
    p[0] = ast.ForStmt(iterable=p[3], capture=p[6], body=p[8])


def p_assignment(p):
    """assignment : postfix_expr EQ expression
                  | postfix_expr PLUS_EQ expression
                  | postfix_expr MINUS_EQ expression
                  | postfix_expr STAR_EQ expression
                  | postfix_expr SLASH_EQ expression
                  | postfix_expr PERCENT_EQ expression"""
    p[0] = ast.AssignStmt(target=p[1], op=p[2], value=p[3])


def p_expr_stmt(p):
    """expr_stmt : expression"""
    p[0] = ast.ExprStmt(p[1])


# =========================
# EXPRESSIONS
# =========================

def p_expression_range(p):
    """expression : expression DOTDOT expression"""
    p[0] = ast.RangeExpr(p[1], p[3])


def p_expression_binary(p):
    """expression : expression PLUS expression
                  | expression MINUS expression
                  | expression STAR expression
                  | expression SLASH expression
                  | expression PERCENT expression
                  | expression EQEQ expression
                  | expression NE expression
                  | expression LT expression
                  | expression LE expression
                  | expression GT expression
                  | expression GE expression
                  | expression ANDAND expression
                  | expression OROR expression"""
    p[0] = ast.BinaryOp(p[2], p[1], p[3])


def p_expression_unary(p):
    """expression : MINUS expression %prec UMINUS
                  | BANG expression
                  | AMP expression
                  | QUESTION expression"""
    p[0] = ast.UnaryOp(p[1], p[2])


def p_expression_postfix(p):
    """expression : postfix_expr"""
    p[0] = p[1]


def p_postfix_expr_primary(p):
    """postfix_expr : primary"""
    p[0] = p[1]


def p_postfix_expr_call(p):
    """postfix_expr : postfix_expr LPAREN args_opt RPAREN"""
    p[0] = ast.CallExpr(callee=p[1], args=p[3])


def p_postfix_expr_field(p):
    """postfix_expr : postfix_expr DOT IDENT"""
    p[0] = ast.FieldAccess(object=p[1], field=p[3])


def p_postfix_expr_index(p):
    """postfix_expr : postfix_expr LBRACKET expression RBRACKET"""
    p[0] = ast.IndexAccess(object=p[1], index=p[3])

def p_postfix_expr_deref(p):
    """postfix_expr : postfix_expr DOT STAR"""
    p[0] = ast.DerefExpr(p[1])

def p_args_opt(p):
    """args_opt : args
                | empty"""
    p[0] = p[1] or []


def p_args(p):
    """args : args COMMA expression
            | expression"""
    if len(p) == 4:
        p[0] = p[1] + [p[3]]
    else:
        p[0] = [p[1]]


# =========================
# PRIMARY (ВАЖНО!)
# =========================

def p_primary_struct_decl(p):
    """primary : STRUCT LBRACE struct_fields_opt RBRACE"""
    p[0] = ast.StructDecl(p[3])


def p_primary_tuple_literal(p):
    """primary : DOT LBRACE args_opt RBRACE"""
    p[0] = ast.TupleLiteral(p[3])


def p_primary_int(p):
    """primary : INT"""
    p[0] = ast.IntLiteral(p[1])


def p_primary_string(p):
    """primary : STRING"""
    p[0] = ast.StringLiteral(p[1])


def p_primary_char(p):
    """primary : CHAR"""
    p[0] = ast.CharLiteral(p[1])


def p_primary_bool(p):
    """primary : TRUE
               | FALSE"""
    p[0] = ast.BoolLiteral(p[1] == "true")


def p_primary_null(p):
    """primary : NULL"""
    p[0] = ast.NullLiteral()


def p_primary_undefined(p):
    """primary : UNDEFINED"""
    p[0] = ast.UndefinedLiteral()


def p_primary_ident(p):
    """primary : IDENT"""
    p[0] = ast.Identifier(p[1])


def p_primary_builtin_ident(p):
    """primary : BUILTIN_IDENT"""
    p[0] = ast.BuiltinIdentifier(p[1])


def p_primary_group(p):
    """primary : LPAREN expression RPAREN"""
    p[0] = p[2]


def p_empty(p):
    """empty :"""
    p[0] = None


def p_error(p):
    if p is None:
        raise ZigParserError("Unexpected end of input")

    raise ZigParserError(
        f"Unexpected token {p.type}({p.value!r}) at line {getattr(p, 'lineno', '?')}"
    )


def build_parser(**kwargs):
    return yacc.yacc(**kwargs)


def parse(source: str):
    lexer = build_lexer()
    parser = build_parser()
    return parser.parse(source, lexer=lexer)