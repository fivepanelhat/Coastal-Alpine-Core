"""
Configuration overlays for the Kiwi Edge stack (Sprint E).

Resolution order (later wins):
  1. defaults
  2. named profile
  3. tenant overlay
  4. session / runtime overlay

CAT constraints:
- No secrets in overlay values (keys containing secret/password/token/key rejected).
- Local-first; pure in-memory merge; no network.
- Soft-import friendly for Weaver / Aether.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Mapping

_SECRET_FRAGMENTS = ("secret", "password", "passwd", "token", "api_key", "apikey", "private_key")


def _is_secret_key(key: str) -> bool:
    k = key.lower().replace("-", "_")
    return any(frag in k for frag in _SECRET_FRAGMENTS)


def _deep_merge(base: dict[str, Any], overlay: Mapping[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    for key, value in overlay.items():
        if _is_secret_key(str(key)):
            raise ValueError(f"Secret-like key rejected in overlay: {key!r}")
        if isinstance(value, Mapping) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)  # type: ignore[arg-type]
        else:
            out[key] = deepcopy(value)
    return out


@dataclass
class ConfigOverlay:
    """Stacked configuration with explicit layers."""

    defaults: dict[str, Any] = field(default_factory=dict)
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)
    tenant: dict[str, Any] = field(default_factory=dict)
    session: dict[str, Any] = field(default_factory=dict)
    active_profile: str | None = None

    def register_profile(self, name: str, data: Mapping[str, Any]) -> None:
        if not name or not str(name).strip():
            raise ValueError("profile name must be non-empty")
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_secret_key(str(k)):
                raise ValueError(f"Secret-like key rejected in profile {name!r}: {k!r}")
            cleaned[str(k)] = deepcopy(v)
        self.profiles[str(name).strip()] = cleaned

    def set_tenant(self, data: Mapping[str, Any]) -> None:
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_secret_key(str(k)):
                raise ValueError(f"Secret-like key rejected in tenant overlay: {k!r}")
            cleaned[str(k)] = deepcopy(v)
        self.tenant = cleaned

    def set_session(self, data: Mapping[str, Any]) -> None:
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if _is_secret_key(str(k)):
                raise ValueError(f"Secret-like key rejected in session overlay: {k!r}")
            cleaned[str(k)] = deepcopy(v)
        self.session = cleaned

    def use_profile(self, name: str | None) -> None:
        if name is None:
            self.active_profile = None
            return
        if name not in self.profiles:
            raise KeyError(f"Unknown profile {name!r}; known: {sorted(self.profiles)}")
        self.active_profile = name

    def resolve(self, profile: str | None = None) -> dict[str, Any]:
        """Merge layers; optional one-shot profile override."""
        merged = deepcopy(self.defaults)
        pname = profile if profile is not None else self.active_profile
        if pname:
            if pname not in self.profiles:
                raise KeyError(f"Unknown profile {pname!r}")
            merged = _deep_merge(merged, self.profiles[pname])
        if self.tenant:
            merged = _deep_merge(merged, self.tenant)
        if self.session:
            merged = _deep_merge(merged, self.session)
        return merged

    def get(self, dotted_key: str, default: Any = None, *, profile: str | None = None) -> Any:
        node: Any = self.resolve(profile=profile)
        for part in dotted_key.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node
