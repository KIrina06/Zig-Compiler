from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# ---------- Program / declarations ----------

@dataclass(slots=True)
class Program:
    declarations: list[Any]


@dataclass(slots=True)
class VarDecl:
    kind: str  # "const" or "var"
    name: str
    type_name: Any | None
    value: Any | None


@dataclass(slots=True)
class FnDecl:
    name: str
    params: list[Param]
    return_type: Any | None
    body: Block


@dataclass(slots=True)
class Param:
    name: str
    type_name: Any


@dataclass(slots=True)
class StructDecl:
    fields: list[StructField]


@dataclass(slots=True)
class StructField:
    name: str
    type_name: Any


# ---------- Types ----------

@dataclass(slots=True)
class NamedType:
    name: str


@dataclass(slots=True)
class OptionalType:
    inner: Any


@dataclass(slots=True)
class PointerType:
    inner: Any


@dataclass(slots=True)
class SliceType:
    inner: Any


@dataclass(slots=True)
class ArrayType:
    size: Any
    inner: Any


# ---------- Statements ----------

@dataclass(slots=True)
class Block:
    statements: list[Any]


@dataclass(slots=True)
class ReturnStmt:
    value: Any | None


@dataclass(slots=True)
class IfStmt:
    condition: Any
    then_block: Block
    else_block: Block | None


@dataclass(slots=True)
class WhileStmt:
    condition: Any
    body: Block


@dataclass(slots=True)
class ForStmt:
    iterable: Any
    capture: str
    body: Block


@dataclass(slots=True)
class BreakStmt:
    pass


@dataclass(slots=True)
class ContinueStmt:
    pass


@dataclass(slots=True)
class AssignStmt:
    target: Any
    op: str
    value: Any


@dataclass(slots=True)
class ExprStmt:
    expr: Any


# ---------- Expressions ----------

@dataclass(slots=True)
class IntLiteral:
    value: int


@dataclass(slots=True)
class StringLiteral:
    value: str


@dataclass(slots=True)
class CharLiteral:
    value: str


@dataclass(slots=True)
class BoolLiteral:
    value: bool


@dataclass(slots=True)
class NullLiteral:
    pass


@dataclass(slots=True)
class UndefinedLiteral:
    pass


@dataclass(slots=True)
class Identifier:
    name: str


@dataclass(slots=True)
class BuiltinIdentifier:
    name: str


@dataclass(slots=True)
class UnaryOp:
    op: str
    expr: Any


@dataclass(slots=True)
class BinaryOp:
    op: str
    left: Any
    right: Any


@dataclass(slots=True)
class CallExpr:
    callee: Any
    args: list[Any]


@dataclass(slots=True)
class FieldAccess:
    object: Any
    field: str


@dataclass(slots=True)
class IndexAccess:
    object: Any
    index: Any

@dataclass(slots=True)
class DerefExpr:
    expr: Any

@dataclass(slots=True)
class RangeExpr:
    start: Any
    end: Any

@dataclass(slots=True)
class TupleLiteral:
    """Zig anonymous tuple literal: .{a, b, c}"""
    items: list[Any]