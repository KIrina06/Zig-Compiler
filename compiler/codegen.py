from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from llvmlite import ir

from compiler import ast


class CodegenError(Exception):
    pass


@dataclass
class StructInfo:
    name: str
    llvm_type: ir.IdentifiedStructType
    field_indices: dict[str, int]
    field_types: dict[str, ir.Type]


class LLVMCodegen:
    def __init__(self):
        self.context = ir.Context()
        self.module = ir.Module(name="zig_subset_module", context=self.context)

        self.loop_stack: list[dict[str, ir.Block]] = []
        self.builder: ir.IRBuilder | None = None
        self.function: ir.Function | None = None
        self.variables: list[dict[str, ir.Value]] = []

        self.structs: dict[str, StructInfo] = {}

        self.i32 = ir.IntType(32)
        self.i1 = ir.IntType(1)
        self.void = ir.VoidType()
        self.i8 = ir.IntType(8)
        self.i8_ptr = self.i8.as_pointer()

        self._declare_printf()

    def _declare_printf(self) -> None:
        printf_ty = ir.FunctionType(self.i32, [self.i8_ptr], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")

    def generate(self, program: ast.Program) -> str:
        self._declare_struct_headers(program)
        self._define_struct_bodies(program)

        for decl in program.declarations:
            if isinstance(decl, ast.FnDecl):
                self._declare_function(decl)

        for decl in program.declarations:
            if isinstance(decl, ast.FnDecl):
                self._emit_function(decl)

        return str(self.module)

    # =========================
    # STRUCTS
    # =========================

    def _declare_struct_headers(self, program: ast.Program) -> None:
        for decl in program.declarations:
            if (
                isinstance(decl, ast.VarDecl)
                and decl.kind == "const"
                and isinstance(decl.value, ast.StructDecl)
            ):
                name = decl.name

                if name in self.structs:
                    raise CodegenError(f"Redeclared struct '{name}'")

                llvm_struct = self.context.get_identified_type(name)

                self.structs[name] = StructInfo(
                    name=name,
                    llvm_type=llvm_struct,
                    field_indices={},
                    field_types={},
                )

    def _define_struct_bodies(self, program: ast.Program) -> None:
        for decl in program.declarations:
            if (
                isinstance(decl, ast.VarDecl)
                and decl.kind == "const"
                and isinstance(decl.value, ast.StructDecl)
            ):
                info = self.structs[decl.name]
                field_llvm_types: list[ir.Type] = []

                for index, field in enumerate(decl.value.fields):
                    llvm_field_type = self._llvm_type(field.type_name)

                    info.field_indices[field.name] = index
                    info.field_types[field.name] = llvm_field_type
                    field_llvm_types.append(llvm_field_type)

                info.llvm_type.set_body(*field_llvm_types)

    # =========================
    # TYPES
    # =========================

    def _llvm_type(self, type_node: Any | None) -> ir.Type:
        if type_node is None:
            return self.void

        if isinstance(type_node, ast.NamedType):
            if type_node.name == "void":
                return self.void
            if type_node.name == "bool":
                return self.i1
            if type_node.name in {"i32", "u32", "usize", "isize", "i64", "u64"}:
                return self.i32

            if type_node.name in self.structs:
                return self.structs[type_node.name].llvm_type

        if isinstance(type_node, ast.PointerType):
            return self._llvm_type(type_node.inner).as_pointer()

        if isinstance(type_node, ast.OptionalType):
            # Для нашего подмножества ?*Node представляем как обычный pointer,
            # где null допустим как значение.
            if isinstance(type_node.inner, ast.PointerType):
                return self._llvm_type(type_node.inner)
            raise CodegenError("Only optional pointers like ?*Node are supported now")

        if isinstance(type_node, ast.ArrayType):
            if not isinstance(type_node.size, ast.IntLiteral):
                raise CodegenError("Only constant-size arrays are supported now")
            return ir.ArrayType(self._llvm_type(type_node.inner), type_node.size.value)

        raise CodegenError(f"Unsupported type: {type_node}")

    # =========================
    # FUNCTIONS
    # =========================

    def _declare_function(self, node: ast.FnDecl) -> None:
        return_ty = self._llvm_type(node.return_type)
        param_tys = [self._llvm_type(param.type_name) for param in node.params]
        fn_ty = ir.FunctionType(return_ty, param_tys)

        if node.name not in self.module.globals:
            ir.Function(self.module, fn_ty, name=node.name)

    def _emit_function(self, node: ast.FnDecl) -> None:
        fn = self.module.globals[node.name]
        self.function = fn

        entry = fn.append_basic_block("entry")
        self.builder = ir.IRBuilder(entry)
        self.variables.append({})

        for llvm_arg, param in zip(fn.args, node.params):
            llvm_arg.name = param.name
            ptr = self.builder.alloca(llvm_arg.type, name=param.name)
            self.builder.store(llvm_arg, ptr)
            self.variables[-1][param.name] = ptr

        self._emit_block(node.body, create_scope=False)

        if not self.builder.block.is_terminated:
            if isinstance(fn.function_type.return_type, ir.VoidType):
                self.builder.ret_void()
            else:
                self.builder.ret(ir.Constant(fn.function_type.return_type, 0))

        self.variables.pop()
        self.builder = None
        self.function = None

    # =========================
    # STATEMENTS
    # =========================

    def _emit_block(self, block: ast.Block, create_scope: bool = True) -> None:
        if create_scope:
            self.variables.append({})

        for stmt in block.statements:
            if self.builder.block.is_terminated:
                break
            self._emit_stmt(stmt)

        if create_scope:
            self.variables.pop()

    def _emit_stmt(self, node: Any) -> None:
        if isinstance(node, ast.VarDecl):
            self._emit_var_decl(node)
        elif isinstance(node, ast.ReturnStmt):
            self._emit_return(node)
        elif isinstance(node, ast.ExprStmt):
            self._emit_expr(node.expr)
        elif isinstance(node, ast.AssignStmt):
            self._emit_assign(node)
        elif isinstance(node, ast.IfStmt):
            self._emit_if(node)
        elif isinstance(node, ast.WhileStmt):
            self._emit_while(node)
        elif isinstance(node, ast.ForStmt):
            self._emit_for(node)
        elif isinstance(node, ast.BreakStmt):
            self._emit_break(node)
        elif isinstance(node, ast.ContinueStmt):
            self._emit_continue(node)
        else:
            raise CodegenError(f"Unsupported statement: {node}")

    def _emit_break(self, node: ast.BreakStmt) -> None:
        if not self.loop_stack:
            raise CodegenError("break outside loop")
        self.builder.branch(self.loop_stack[-1]["break"])


    def _emit_continue(self, node: ast.ContinueStmt) -> None:
        if not self.loop_stack:
            raise CodegenError("continue outside loop")
        self.builder.branch(self.loop_stack[-1]["continue"])
        
    def _emit_var_decl(self, node: ast.VarDecl) -> None:
        llvm_ty = self._llvm_type(node.type_name)

        if isinstance(llvm_ty, ir.VoidType):
            raise CodegenError(f"Variable '{node.name}' cannot have void type")

        ptr = self.builder.alloca(llvm_ty, name=node.name)

        if node.value is not None and not isinstance(node.value, ast.UndefinedLiteral):
            value = self._emit_expr(node.value)
            self.builder.store(value, ptr)
        else:
            self.builder.store(ir.Constant(llvm_ty, None), ptr)

        self.variables[-1][node.name] = ptr

    def _emit_return(self, node: ast.ReturnStmt) -> None:
        if node.value is None:
            self.builder.ret_void()
        else:
            self.builder.ret(self._emit_expr(node.value))

    def _emit_assign(self, node: ast.AssignStmt) -> None:
        ptr = self._emit_lvalue(node.target)
        value = self._emit_expr(node.value, expected_type=ptr.type.pointee)

        if node.op == "=":
            self.builder.store(value, ptr)
            return

        old = self.builder.load(ptr, name="assign_old")

        if node.op == "+=":
            new_value = self.builder.add(old, value)
        elif node.op == "-=":
            new_value = self.builder.sub(old, value)
        elif node.op == "*=":
            new_value = self.builder.mul(old, value)
        elif node.op == "/=":
            new_value = self.builder.sdiv(old, value)
        elif node.op == "%=":
            new_value = self.builder.srem(old, value)
        else:
            raise CodegenError(f"Unsupported assignment operator: {node.op}")

        self.builder.store(new_value, ptr)

    def _emit_if(self, node: ast.IfStmt) -> None:
        cond = self._to_bool(self._emit_expr(node.condition))

        then_bb = self.function.append_basic_block("if.then")
        else_bb = self.function.append_basic_block("if.else")
        merge_bb = self.function.append_basic_block("if.end")

        self.builder.cbranch(cond, then_bb, else_bb)

        self.builder.position_at_end(then_bb)
        self._emit_block(node.then_block)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)

        self.builder.position_at_end(else_bb)
        if node.else_block is not None:
            self._emit_block(node.else_block)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)

        self.builder.position_at_end(merge_bb)

    def _emit_while(self, node: ast.WhileStmt) -> None:
        cond_bb = self.function.append_basic_block("while.cond")
        body_bb = self.function.append_basic_block("while.body")
        end_bb = self.function.append_basic_block("while.end")

        self.builder.branch(cond_bb)

        self.builder.position_at_end(cond_bb)
        cond = self._to_bool(self._emit_expr(node.condition))
        self.builder.cbranch(cond, body_bb, end_bb)

        self.loop_stack.append({
            "break": end_bb,
            "continue": cond_bb,
        })

        self.builder.position_at_end(body_bb)
        self._emit_block(node.body)

        if not self.builder.block.is_terminated:
            self.builder.branch(cond_bb)

        self.loop_stack.pop()
        self.builder.position_at_end(end_bb)

    def _emit_for(self, node: ast.ForStmt) -> None:
        if not isinstance(node.iterable, ast.RangeExpr):
            raise CodegenError("Only for-loops over ranges are supported now")

        start_value = self._emit_expr(node.iterable.start)
        end_value = self._emit_expr(node.iterable.end)

        self.variables.append({})

        index_ptr = self.builder.alloca(self.i32, name=node.capture)
        self.builder.store(start_value, index_ptr)
        self.variables[-1][node.capture] = index_ptr

        cond_bb = self.function.append_basic_block("for.cond")
        body_bb = self.function.append_basic_block("for.body")
        inc_bb = self.function.append_basic_block("for.inc")
        end_bb = self.function.append_basic_block("for.end")

        self.builder.branch(cond_bb)

        self.builder.position_at_end(cond_bb)
        current = self.builder.load(index_ptr, name=f"{node.capture}.value")
        cond = self.builder.icmp_signed("<", current, end_value)
        self.builder.cbranch(cond, body_bb, end_bb)

        self.loop_stack.append({
            "break": end_bb,
            "continue": inc_bb,
        })

        self.builder.position_at_end(body_bb)
        self._emit_block(node.body)

        if not self.builder.block.is_terminated:
            self.builder.branch(inc_bb)

        self.builder.position_at_end(inc_bb)
        current = self.builder.load(index_ptr, name=f"{node.capture}.next")
        next_value = self.builder.add(current, ir.Constant(self.i32, 1))
        self.builder.store(next_value, index_ptr)
        self.builder.branch(cond_bb)

        self.loop_stack.pop()

        self.builder.position_at_end(end_bb)
        self.variables.pop()

    # =========================
    # EXPRESSIONS
    # =========================

    def _emit_expr(self, node: Any, expected_type: ir.Type | None = None) -> ir.Value:
        if isinstance(node, ast.IntLiteral):
            return ir.Constant(expected_type or self.i32, node.value)
        
        if isinstance(node, ast.UnaryOp):
            return self._emit_unary(node, expected_type=expected_type)

        if isinstance(node, ast.DerefExpr):
            ptr = self._emit_expr(node.expr)
            return self.builder.load(ptr, name="deref")

        if isinstance(node, ast.BoolLiteral):
            return ir.Constant(self.i1, int(node.value))

        if isinstance(node, ast.NullLiteral):
            if expected_type is None or not isinstance(expected_type, ir.PointerType):
                raise CodegenError("null requires pointer expected type")
            return ir.Constant(expected_type, None)

        if isinstance(node, ast.UndefinedLiteral):
            if expected_type is None:
                raise CodegenError("undefined requires expected type")
            return ir.Constant(expected_type, None)

        if isinstance(node, ast.Identifier):
            ptr = self._lookup_var(node.name)
            return self.builder.load(ptr, name=node.name)

        if isinstance(node, ast.IndexAccess):
            ptr = self._emit_lvalue(node)
            return self.builder.load(ptr, name="array_item")

        if isinstance(node, ast.FieldAccess):
            ptr = self._emit_lvalue(node)
            return self.builder.load(ptr, name=f"{node.field}.value")

        if isinstance(node, ast.BinaryOp):
            return self._emit_binary(node)

        if isinstance(node, ast.CallExpr):
            return self._emit_call(node)

        raise CodegenError(f"Unsupported expression: {node}")

    def _emit_unary(self, node: ast.UnaryOp, expected_type: ir.Type | None = None) -> ir.Value:
        if node.op == "-":
            value = self._emit_expr(node.expr)
            return self.builder.neg(value)

        if node.op == "!":
            value = self._to_bool(self._emit_expr(node.expr))
            return self.builder.xor(value, ir.Constant(self.i1, 1))

        if node.op == "&":
            return self._emit_lvalue(node.expr)

        raise CodegenError(f"Unsupported unary operator: {node.op}")

    def _emit_lvalue(self, node: Any) -> ir.Value:
        if isinstance(node, ast.Identifier):
            return self._lookup_var(node.name)

        if isinstance(node, ast.DerefExpr):
            ptr = self._emit_expr(node.expr)

            if not isinstance(ptr.type, ir.PointerType):
                raise CodegenError("Cannot dereference non-pointer value")

            return ptr

        if isinstance(node, ast.IndexAccess):
            base_ptr = self._emit_lvalue(node.object)
            index = self._emit_expr(node.index)
            zero = ir.Constant(self.i32, 0)

            return self.builder.gep(
                base_ptr,
                [zero, index],
                inbounds=True,
                name="array_index_ptr",
            )

        if isinstance(node, ast.FieldAccess):
            object_ptr = self._emit_lvalue(node.object)
            struct_type = object_ptr.type.pointee

            info = self._find_struct_info_by_llvm_type(struct_type)
            if info is None:
                raise CodegenError(f"Field access on non-struct value: {node.field}")

            if node.field not in info.field_indices:
                raise CodegenError(f"Unknown field '{node.field}' in struct '{info.name}'")

            field_index = info.field_indices[node.field]

            return self.builder.gep(
                object_ptr,
                [
                    ir.Constant(self.i32, 0),
                    ir.Constant(self.i32, field_index),
                ],
                inbounds=True,
                name=f"{node.field}.ptr",
            )

        raise CodegenError(f"Unsupported assignment target: {node}")

    def _find_struct_info_by_llvm_type(self, llvm_type: ir.Type) -> StructInfo | None:
        for info in self.structs.values():
            if info.llvm_type is llvm_type or str(info.llvm_type) == str(llvm_type):
                return info
        return None

    def _emit_binary(self, node: ast.BinaryOp) -> ir.Value:
        left = self._emit_expr(node.left)
        right = self._emit_expr(node.right, expected_type=left.type)

        if node.op == "+":
            return self.builder.add(left, right)
        if node.op == "-":
            return self.builder.sub(left, right)
        if node.op == "*":
            return self.builder.mul(left, right)
        if node.op == "/":
            return self.builder.sdiv(left, right)
        if node.op == "%":
            return self.builder.srem(left, right)

        if node.op == "<":
            return self.builder.icmp_signed("<", left, right)
        if node.op == "<=":
            return self.builder.icmp_signed("<=", left, right)
        if node.op == ">":
            return self.builder.icmp_signed(">", left, right)
        if node.op == ">=":
            return self.builder.icmp_signed(">=", left, right)
        if node.op == "==":
            return self.builder.icmp_signed("==", left, right)
        if node.op == "!=":
            return self.builder.icmp_signed("!=", left, right)
        
        if node.op == "&&":
            return self.builder.and_(self._to_bool(left), self._to_bool(right))

        if node.op == "||":
            return self.builder.or_(self._to_bool(left), self._to_bool(right))

        raise CodegenError(f"Unsupported binary operator: {node.op}")

    def _emit_call(self, node: ast.CallExpr) -> ir.Value:
        if self._is_std_debug_print(node.callee):
            return self._emit_print(node)

        if not isinstance(node.callee, ast.Identifier):
            raise CodegenError("Only direct function calls are supported now")

        fn_name = node.callee.name

        if fn_name not in self.module.globals:
            raise CodegenError(f"Unknown function: {fn_name}")

        fn = self.module.globals[fn_name]
        args = [
            self._emit_expr(arg, expected_type=param.type)
            for arg, param in zip(node.args, fn.args)
        ]

        return self.builder.call(fn, args, name=f"call_{fn_name}")

    # =========================
    # PRINT
    # =========================

    def _emit_print(self, node: ast.CallExpr) -> ir.Value:
        if not node.args:
            raise CodegenError("std.debug.print requires a format string")

        fmt_node = node.args[0]

        if not isinstance(fmt_node, ast.StringLiteral):
            raise CodegenError("First argument of std.debug.print must be a string")

        fmt = self._zig_string_to_python(fmt_node.value)
        fmt_ptr = self._global_string(fmt)

        printf_args = [fmt_ptr]

        if len(node.args) >= 2:
            second = node.args[1]

            if isinstance(second, ast.TupleLiteral):
                for item in second.items:
                    printf_args.append(self._emit_expr(item))
            else:
                printf_args.append(self._emit_expr(second))

        return self.builder.call(self.printf, printf_args, name="printf_call")

    def _is_std_debug_print(self, callee: Any) -> bool:
        return (
            isinstance(callee, ast.FieldAccess)
            and callee.field == "print"
            and isinstance(callee.object, ast.FieldAccess)
            and callee.object.field == "debug"
            and isinstance(callee.object.object, ast.Identifier)
            and callee.object.object.name == "std"
        )

    def _global_string(self, text: str) -> ir.Value:
        raw = bytearray(text.encode("utf-8")) + b"\x00"
        const_ty = ir.ArrayType(self.i8, len(raw))
        name = f".str.{len(self.module.globals)}"

        global_var = ir.GlobalVariable(self.module, const_ty, name=name)
        global_var.global_constant = True
        global_var.initializer = ir.Constant(const_ty, raw)

        zero = ir.Constant(self.i32, 0)

        return self.builder.gep(
            global_var,
            [zero, zero],
            inbounds=True,
            name="strptr",
        )

    def _zig_string_to_python(self, value: str) -> str:
        inner = value[1:-1]
        inner = inner.replace("{}", "%d")
        return bytes(inner, "utf-8").decode("unicode_escape")

    # =========================
    # HELPERS
    # =========================

    def _lookup_var(self, name: str) -> ir.Value:
        for scope in reversed(self.variables):
            if name in scope:
                return scope[name]

        raise CodegenError(f"Unknown variable: {name}")

    def _to_bool(self, value: ir.Value) -> ir.Value:
        if isinstance(value.type, ir.IntType) and value.type.width == 1:
            return value

        return self.builder.icmp_signed("!=", value, ir.Constant(value.type, 0))


def generate_llvm_ir(program: ast.Program) -> str:
    return LLVMCodegen().generate(program)