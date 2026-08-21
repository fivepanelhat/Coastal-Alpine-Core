"""
PTC / Code Mode — programmatic tool calling (Sprint E).

Agents may emit a small Python snippet that calls registered tools by name
instead of pure JSON tool-call lists. Execution is restricted:

- No imports, no builtins except a whitelist
- Only `tools.<name>(**kwargs)` style calls via a provided Tools proxy
- No file/network/os access from the snippet itself
- Optional HITL gate callback before run

CAT: local-first, fail-closed, no secrets in traces.
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

logger = logging.getLogger("coastal_alpine_core.code_mode")

ToolFn = Callable[..., Any]
HitlFn = Callable[[str], bool]


@dataclass
class CodeModeResult:
    success: bool
    output: Any = None
    error: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


class _ToolsProxy:
    def __init__(self, registry: Mapping[str, ToolFn], call_log: list[dict[str, Any]]):
        self._registry = registry
        self._log = call_log

    def __getattr__(self, name: str) -> Callable[..., Any]:
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._registry:
            raise AttributeError(f"Unknown tool {name!r}")

        def _call(**kwargs: Any) -> Any:
            self._log.append({"tool": name, "kwargs_keys": sorted(kwargs.keys())})
            return self._registry[name](**kwargs)

        return _call


_ALLOWED_NODE_TYPES = (
    ast.Module,
    ast.Expr,
    ast.Assign,
    ast.AugAssign,
    ast.AnnAssign,
    ast.Return,
    ast.If,
    ast.For,
    ast.While,
    ast.Break,
    ast.Continue,
    ast.Pass,
    ast.Call,
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Constant,
    ast.List,
    ast.Tuple,
    ast.Dict,
    ast.Set,
    ast.UnaryOp,
    ast.BinOp,
    ast.BoolOp,
    ast.Compare,
    ast.Attribute,
    ast.keyword,
    ast.arguments,
    ast.arg,
    ast.FunctionDef,
    ast.Lambda,
    ast.comprehension,
    ast.ListComp,
    ast.DictComp,
    ast.SetComp,
    ast.Subscript,
    ast.Slice,
    ast.IfExp,
    ast.JoinedStr,
    ast.FormattedValue,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
    ast.Not,
    ast.And,
    ast.Or,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.In,
    ast.NotIn,
    ast.Is,
    ast.IsNot,
)


def _validate_ast(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("Imports are not allowed in code mode")
        if not isinstance(node, _ALLOWED_NODE_TYPES):
            raise ValueError(f"Disallowed syntax: {type(node).__name__}")
        if isinstance(node, ast.Attribute) and str(node.attr).startswith("_"):
            raise ValueError("Private/dunder attribute access blocked")
        if isinstance(node, ast.Name) and node.id.startswith("__"):
            raise ValueError("Dunder names blocked")
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            raise ValueError("Decorators not allowed in code mode")


class CodeModeRunner:
    """Execute restricted agent-authored snippets against a tool registry."""

    def __init__(
        self,
        tools: Mapping[str, ToolFn],
        *,
        hitl: HitlFn | None = None,
        max_chars: int = 4000,
    ):
        self.tools = dict(tools)
        self.hitl = hitl
        self.max_chars = max_chars

    def run(self, source: str) -> CodeModeResult:
        src = (source or "").strip()
        if not src:
            return CodeModeResult(success=False, error="empty_source")
        if len(src) > self.max_chars:
            return CodeModeResult(success=False, error="source_too_long")

        if self.hitl is not None:
            try:
                if not self.hitl(src):
                    return CodeModeResult(success=False, error="hitl_rejected")
            except Exception as exc:
                return CodeModeResult(success=False, error=f"hitl_error:{exc}")

        try:
            tree = ast.parse(src, mode="exec")
            _validate_ast(tree)
        except Exception as exc:
            return CodeModeResult(success=False, error=f"parse:{exc}")

        call_log: list[dict[str, Any]] = []
        proxy = _ToolsProxy(self.tools, call_log)

        safe_builtins = {
            "True": True,
            "False": False,
            "None": None,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "min": min,
            "max": max,
            "sum": sum,
            "sorted": sorted,
            "range": range,
            "enumerate": enumerate,
            "zip": zip,
            "print": lambda *a, **k: None,
        }

        globals_dict: dict[str, Any] = {"__builtins__": safe_builtins, "tools": proxy}
        locals_dict: dict[str, Any] = {}

        try:
            compiled = compile(tree, "<aether_code_mode>", "exec")
            exec(compiled, globals_dict, locals_dict)  # noqa: S102 — intentional sandbox
            output = locals_dict.get("result", locals_dict.get("output"))
            return CodeModeResult(success=True, output=output, tool_calls=call_log)
        except Exception as exp:
            logger.debug("Code mode execution failed: %s", exp)
            return CodeModeResult(
                success=False,
                error=str(exp)[:300],
                tool_calls=call_log,
            )
