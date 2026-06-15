from __future__ import annotations

import json
from dataclasses import fields, is_dataclass
from typing import Any


class ASTPrinter:
    def __init__(self, max_leaf_length: int = 80):
        self.max_leaf_length = max_leaf_length

    def format(self, node: Any) -> str:
        lines: list[str] = []
        self._visit(node, lines, prefix="", label=None, is_last=True)
        return "\n".join(lines)

    def _visit(
        self,
        value: Any,
        lines: list[str],
        prefix: str,
        label: str | None,
        is_last: bool,
    ) -> None:
        connector = "└── " if is_last else "├── "
        line_prefix = "" if prefix == "" and label is None else prefix + connector

        if is_dataclass(value):
            header = value.__class__.__name__
            lines.append(
                header if label is None and prefix == ""
                else f"{line_prefix}{label + ': ' if label else ''}{header}"
            )

            child_prefix = prefix + ("    " if is_last else "│   ")
            node_fields = fields(value)

            for index, field in enumerate(node_fields):
                self._visit(
                    getattr(value, field.name),
                    lines,
                    child_prefix,
                    label=field.name,
                    is_last=index == len(node_fields) - 1,
                )
            return

        if isinstance(value, list):
            lines.append(f"{line_prefix}{label + ': ' if label else ''}[{len(value)}]")

            child_prefix = prefix + ("    " if is_last else "│   ")

            for index, item in enumerate(value):
                self._visit(
                    item,
                    lines,
                    child_prefix,
                    label=f"[{index}]",
                    is_last=index == len(value) - 1,
                )
            return

        lines.append(f"{line_prefix}{label + ': ' if label else ''}{self._render_leaf(value)}")

    def _render_leaf(self, value: Any) -> str:
        if value is None:
            return "None"

        if isinstance(value, str):
            text = repr(value)
        else:
            text = str(value)

        if len(text) > self.max_leaf_length:
            return text[: self.max_leaf_length - 3] + "..."

        return text


def ast_to_dict(node: Any) -> Any:
    if is_dataclass(node):
        result = {"node": node.__class__.__name__}
        for field in fields(node):
            result[field.name] = ast_to_dict(getattr(node, field.name))
        return result

    if isinstance(node, list):
        return [ast_to_dict(item) for item in node]

    return node


def format_ast(node: Any, max_leaf_length: int = 80) -> str:
    return ASTPrinter(max_leaf_length=max_leaf_length).format(node)


def format_ast_json(node: Any) -> str:
    return json.dumps(ast_to_dict(node), ensure_ascii=False, indent=2)


def format_ast_dot(node: Any) -> str:
    lines = ["digraph AST {", "  node [shape=box];"]
    counter = 0

    def next_id() -> str:
        nonlocal counter
        counter += 1
        return f"n{counter}"

    def escape(text: str) -> str:
        return text.replace("\\", "\\\\").replace('"', '\\"')

    def visit(value: Any, label: str | None = None) -> str:
        node_id = next_id()

        if is_dataclass(value):
            title = value.__class__.__name__
            if label:
                title = f"{label}: {title}"

            lines.append(f'  {node_id} [label="{escape(title)}"];')

            for field in fields(value):
                child_id = visit(getattr(value, field.name), field.name)
                lines.append(f"  {node_id} -> {child_id};")

            return node_id

        if isinstance(value, list):
            title = f"{label}: [{len(value)}]" if label else f"[{len(value)}]"
            lines.append(f'  {node_id} [label="{escape(title)}"];')

            for index, item in enumerate(value):
                child_id = visit(item, f"[{index}]")
                lines.append(f"  {node_id} -> {child_id};")

            return node_id

        title = f"{label}: {value!r}" if label else repr(value)
        lines.append(f'  {node_id} [label="{escape(title)}"];')
        return node_id

    visit(node)
    lines.append("}")
    return "\n".join(lines)