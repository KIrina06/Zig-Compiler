from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from compiler import ast


class SemanticError(Exception):
    pass


@dataclass
class Symbol:
    name: str
    kind: str          # var, const, fn, param, type
    type_name: Any | None = None
    node: Any | None = None


class Scope:
    def __init__(self, parent: Scope | None = None, name: str = "scope"):
        self.parent = parent
        self.name = name
        self.symbols: dict[str, Symbol] = {}

    def define(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            raise SemanticError(f"Redeclaration of '{symbol.name}' in {self.name}")
        self.symbols[symbol.name] = symbol

    def resolve(self, name: str) -> Symbol | None:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.resolve(name)
        return None


class SemanticAnalyzer:
    def __init__(self):
        self.global_scope = Scope(name="global")
        self.current_scope = self.global_scope
        self.current_function: ast.FnDecl | None = None

    def analyze(self, program: ast.Program) -> Scope:
        self._define_builtin_symbols()
        self._declare_global_symbols(program)
        self.visit(program)
        return self.global_scope

    def visit_DerefExpr(self, node: ast.DerefExpr) -> None:
        self.visit(node.expr)

    def _define_builtin_symbols(self) -> None:
        for type_name in [
            "void", "bool", "usize", "isize",
            "u8", "u16", "u32", "u64",
            "i8", "i16", "i32", "i64",
        ]:
            self.global_scope.define(Symbol(type_name, "type"))

        self.global_scope.define(Symbol("std", "const"))

    def _declare_global_symbols(self, program: ast.Program) -> None:
        for decl in program.declarations:
            if isinstance(decl, ast.FnDecl):
                self.global_scope.define(
                    Symbol(
                        name=decl.name,
                        kind="fn",
                        type_name=decl.return_type,
                        node=decl,
                    )
                )

            elif isinstance(decl, ast.VarDecl):
                # const std = @import("std");
                # std уже добавлен как builtin, поэтому не объявляем его повторно.
                if decl.name == "std":
                    continue

                # Zig-стиль:
                # const Node = struct { ... };
                # Для нашего компилятора это объявление типа, а не обычной const-переменной.
                if isinstance(decl.value, ast.StructDecl):
                    self.global_scope.define(
                        Symbol(
                            name=decl.name,
                            kind="type",
                            type_name=decl.value,
                            node=decl.value,
                        )
                    )
                    continue

                self.global_scope.define(
                    Symbol(
                        name=decl.name,
                        kind=decl.kind,
                        type_name=decl.type_name,
                        node=decl,
                    )
                )

    def push_scope(self, name: str) -> None:
        self.current_scope = Scope(parent=self.current_scope, name=name)

    def pop_scope(self) -> None:
        if self.current_scope.parent is None:
            raise SemanticError("Cannot pop global scope")
        self.current_scope = self.current_scope.parent

    def visit(self, node: Any) -> None:
        method_name = f"visit_{node.__class__.__name__}"
        method = getattr(self, method_name, self.generic_visit)
        method(node)

    def generic_visit(self, node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                self.visit(item)
            return

        if hasattr(node, "__dataclass_fields__"):
            for field_name in node.__dataclass_fields__:
                value = getattr(node, field_name)
                if isinstance(value, list):
                    for item in value:
                        self.visit(item)
                elif hasattr(value, "__dataclass_fields__"):
                    self.visit(value)

    def visit_Program(self, node: ast.Program) -> None:
        for decl in node.declarations:
            self.visit(decl)

    def visit_FnDecl(self, node: ast.FnDecl) -> None:
        previous_function = self.current_function
        self.current_function = node

        self.push_scope(f"fn {node.name}")

        for param in node.params:
            self.current_scope.define(
                Symbol(
                    name=param.name,
                    kind="param",
                    type_name=param.type_name,
                    node=param,
                )
            )
            self.visit(param.type_name)

        if node.return_type is not None:
            self.visit(node.return_type)

        self.visit(node.body)

        self.pop_scope()
        self.current_function = previous_function

    def visit_Block(self, node: ast.Block) -> None:
        self.push_scope("block")

        for statement in node.statements:
            self.visit(statement)

        self.pop_scope()

    def visit_VarDecl(self, node: ast.VarDecl) -> None:
        if node.type_name is not None:
            self.visit(node.type_name)

        if node.value is not None:
            self.visit(node.value)

        # Глобальные объявления уже зарегистрированы в _declare_global_symbols.
        # Поэтому на втором проходе не объявляем их повторно.
        if self.current_scope is self.global_scope:
            return

        self.current_scope.define(
            Symbol(
                name=node.name,
                kind=node.kind,
                type_name=node.type_name,
                node=node,
            )
        )

    def visit_Param(self, node: ast.Param) -> None:
        self.visit(node.type_name)

    def visit_NamedType(self, node: ast.NamedType) -> None:
        symbol = self.current_scope.resolve(node.name)
        if symbol is None or symbol.kind not in {"type", "const"}:
            raise SemanticError(f"Unknown type '{node.name}'")

    def visit_OptionalType(self, node: ast.OptionalType) -> None:
        self.visit(node.inner)

    def visit_PointerType(self, node: ast.PointerType) -> None:
        self.visit(node.inner)

    def visit_SliceType(self, node: ast.SliceType) -> None:
        self.visit(node.inner)

    def visit_ArrayType(self, node: ast.ArrayType) -> None:
        self.visit(node.size)
        self.visit(node.inner)

    def visit_StructDecl(self, node: ast.StructDecl) -> None:
        names: set[str] = set()

        for field in node.fields:
            if field.name in names:
                raise SemanticError(f"Duplicate struct field '{field.name}'")
            names.add(field.name)
            self.visit(field.type_name)

    def visit_ReturnStmt(self, node: ast.ReturnStmt) -> None:
        if self.current_function is None:
            raise SemanticError("Return outside function")

        if node.value is not None:
            self.visit(node.value)

    def visit_IfStmt(self, node: ast.IfStmt) -> None:
        self.visit(node.condition)
        self.visit(node.then_block)

        if node.else_block is not None:
            self.visit(node.else_block)

    def visit_WhileStmt(self, node: ast.WhileStmt) -> None:
        self.visit(node.condition)
        self.visit(node.body)

    def visit_ForStmt(self, node: ast.ForStmt) -> None:
        self.visit(node.iterable)

        self.push_scope("for")
        self.current_scope.define(Symbol(node.capture, "var"))
        self.visit(node.body)
        self.pop_scope()

    def visit_AssignStmt(self, node: ast.AssignStmt) -> None:
        self.visit(node.target)
        self.visit(node.value)

        if isinstance(node.target, ast.Identifier):
            symbol = self.current_scope.resolve(node.target.name)

            if symbol is not None and symbol.kind == "const":
                raise SemanticError(f"Cannot assign to const '{node.target.name}'")

    def visit_ExprStmt(self, node: ast.ExprStmt) -> None:
        self.visit(node.expr)

    def visit_Identifier(self, node: ast.Identifier) -> None:
        symbol = self.current_scope.resolve(node.name)

        if symbol is None:
            raise SemanticError(f"Use of undeclared identifier '{node.name}'")

    def visit_BuiltinIdentifier(self, node: ast.BuiltinIdentifier) -> None:
        pass

    def visit_IntLiteral(self, node: ast.IntLiteral) -> None:
        pass

    def visit_StringLiteral(self, node: ast.StringLiteral) -> None:
        pass

    def visit_CharLiteral(self, node: ast.CharLiteral) -> None:
        pass

    def visit_BoolLiteral(self, node: ast.BoolLiteral) -> None:
        pass

    def visit_NullLiteral(self, node: ast.NullLiteral) -> None:
        pass

    def visit_UndefinedLiteral(self, node: ast.UndefinedLiteral) -> None:
        pass

    def visit_UnaryOp(self, node: ast.UnaryOp) -> None:
        self.visit(node.expr)

    def visit_BinaryOp(self, node: ast.BinaryOp) -> None:
        self.visit(node.left)
        self.visit(node.right)

    def visit_CallExpr(self, node: ast.CallExpr) -> None:
        self.visit(node.callee)

        for arg in node.args:
            self.visit(arg)

    def visit_FieldAccess(self, node: ast.FieldAccess) -> None:
        self.visit(node.object)

    def visit_IndexAccess(self, node: ast.IndexAccess) -> None:
        self.visit(node.object)
        self.visit(node.index)

    def visit_RangeExpr(self, node: ast.RangeExpr) -> None:
        self.visit(node.start)
        self.visit(node.end)

    def visit_TupleLiteral(self, node: ast.TupleLiteral) -> None:
        for item in node.items:
            self.visit(item)


def analyze(program: ast.Program) -> Scope:
    return SemanticAnalyzer().analyze(program)