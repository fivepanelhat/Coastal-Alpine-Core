"""
Dependency-declared skill / agent loading (Sprint E).

Skills declare `depends_on: [other_skill, ...]` in metadata. This module
produces a stable topological load order and detects cycles / missing deps.

CAT: pure functions, no I/O, no secrets.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class SkillGraphError(ValueError):
    """Invalid skill dependency graph."""


def _deps_of(meta: Mapping[str, Any]) -> list[str]:
    raw = meta.get("depends_on") or meta.get("dependencies") or []
    if isinstance(raw, str):
        return [raw]
    if not isinstance(raw, (list, tuple)):
        return []
    return [str(x).strip() for x in raw if str(x).strip()]


def resolve_skill_order(
    skills: Mapping[str, Mapping[str, Any]],
    *,
    required: Iterable[str] | None = None,
) -> list[str]:
    """
    Return skill names in dependency-safe load order.

    If `required` is set, only those skills (and their transitive deps) are included.
    Raises SkillGraphError on cycles or missing dependencies.
    """
    if not skills:
        return []

    names = set(skills.keys())
    dep_map: dict[str, list[str]] = {}
    for name, meta in skills.items():
        deps = _deps_of(meta)
        missing = [d for d in deps if d not in names]
        if missing:
            raise SkillGraphError(
                f"Skill {name!r} depends on missing skill(s): {missing}"
            )
        dep_map[name] = deps

    if required is not None:
        need: set[str] = set()
        stack = list(required)
        while stack:
            n = stack.pop()
            if n in need:
                continue
            if n not in names:
                raise SkillGraphError(f"Required skill missing: {n!r}")
            need.add(n)
            stack.extend(dep_map.get(n, []))
        dep_map = {k: v for k, v in dep_map.items() if k in need}

    # Kahn topological sort (stable by sorted name for determinism)
    incoming: dict[str, int] = {n: 0 for n in dep_map}
    for n, deps in dep_map.items():
        for d in deps:
            if d in incoming:
                incoming[n] = incoming.get(n, 0)  # ensure key
        for d in deps:
            # edge d -> n means d must load first; increase indegree of n
            pass
    indegree = {n: 0 for n in dep_map}
    for n, deps in dep_map.items():
        indegree[n] = len([d for d in deps if d in dep_map])

    ready = sorted([n for n, deg in indegree.items() if deg == 0])
    order: list[str] = []
    while ready:
        n = ready.pop(0)
        order.append(n)
        for m, deps in dep_map.items():
            if n in deps and m not in order:
                indegree[m] -= 1
                if indegree[m] == 0:
                    ready.append(m)
                    ready.sort()

    if len(order) != len(dep_map):
        cyclic = sorted(set(dep_map) - set(order))
        raise SkillGraphError(f"Cyclic skill dependencies involving: {cyclic}")
    return order


def validate_skill_graph(skills: Mapping[str, Mapping[str, Any]]) -> list[str]:
    """Validate and return full load order."""
    return resolve_skill_order(skills)
