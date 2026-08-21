"""
LLM provider seams for the Kiwi Edge stack (Sprint A Phase 2).

CAT / Te Mana Raraunga constraints:
- Local-first: default provider is on-box Ollama (no cloud keys required).
- No secrets in provider configs or event payloads.
- Soft registry: consumers soft-import; missing Core must not break Weaver/Aether.
- HITL evidence only: optional SessionEvent emission is audit, not control.

Design:
- LLMProvider Protocol — common surface for generate / chat / health.
- ProviderProfile — edge defaults (model, temperature, timeouts).
- get_provider() — factory; today only "ollama" (SovereignOllamaClient).
- Future providers register without changing Weaver/Aether call sites.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from coastal_alpine_core.ollama_client import OllamaResponse, SovereignOllamaClient

# ---------------------------------------------------------------------------
# Profiles (edge-first defaults)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProviderProfile:
    """Named generation profile. Safe to serialise; contains no secrets."""

    name: str
    provider: str = "ollama"
    model: str = "gemma4:e4b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.2
    num_predict: int = 256
    timeout: float = 30.0
    max_retries: int = 3
    extra: dict[str, Any] = field(default_factory=dict)


# Built-in profiles — local edge only. Cloud profiles are out of scope for Phase 2.
PROFILES: dict[str, ProviderProfile] = {
    "edge-default": ProviderProfile(name="edge-default"),
    "edge-fast": ProviderProfile(
        name="edge-fast",
        model="gemma4:e4b",
        num_predict=128,
        timeout=15.0,
        max_retries=2,
    ),
    "edge-coder": ProviderProfile(
        name="edge-coder",
        model="qwen2.5-coder:7b",
        num_predict=512,
        timeout=60.0,
    ),
}


def get_profile(name: str = "edge-default") -> ProviderProfile:
    """Return a built-in profile or raise KeyError."""
    if name not in PROFILES:
        raise KeyError(f"Unknown provider profile {name!r}; known: {sorted(PROFILES)}")
    return PROFILES[name]


# ---------------------------------------------------------------------------
# Protocol
# ---------------------------------------------------------------------------


@runtime_checkable
class LLMProvider(Protocol):
    """
    Minimal shared surface for edge LLM backends.

    Implementations must be local-first and fail closed to deterministic
    offline behaviour where possible (see SovereignOllamaClient).
    """

    def check_health(self) -> bool:
        """True when the backend is reachable."""
        ...

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        options: dict[str, Any] | None = None,
        retries: int | None = None,
    ) -> OllamaResponse | dict[str, Any]:
        """Completion; returns a dict-like response with at least 'response'."""
        ...

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        """Plain-text completion."""
        ...

    def chat(self, prompt: str, **kwargs: Any) -> str:
        """Alias for invoke (chat-style API)."""
        ...


# ---------------------------------------------------------------------------
# Factory / registry
# ---------------------------------------------------------------------------

_PROVIDER_REGISTRY: dict[str, type] = {
    "ollama": SovereignOllamaClient,
}


def register_provider(name: str, cls: type) -> None:
    """Register a custom provider class (advanced / tests)."""
    if not name or not str(name).strip():
        raise ValueError("provider name must be non-empty")
    _PROVIDER_REGISTRY[str(name).strip().lower()] = cls


def list_providers() -> list[str]:
    return sorted(_PROVIDER_REGISTRY)


def get_provider(
    name: str = "ollama",
    *,
    profile: str | ProviderProfile | None = None,
    host: str | None = None,
    default_model: str | None = None,
    timeout: float | None = None,
    **kwargs: Any,
) -> LLMProvider:
    """
    Construct a provider instance.

    Resolution order for host / model / timeout:
    explicit kwargs > profile fields > provider class defaults.
    """
    key = str(name).strip().lower()
    if key not in _PROVIDER_REGISTRY:
        raise KeyError(
            f"Unknown provider {name!r}; registered: {list_providers()}"
        )

    prof: ProviderProfile | None = None
    if isinstance(profile, ProviderProfile):
        prof = profile
    elif isinstance(profile, str):
        prof = get_profile(profile)

    cls = _PROVIDER_REGISTRY[key]
    init_kwargs: dict[str, Any] = dict(kwargs)

    # SovereignOllamaClient signature: host, default_model, timeout, ...
    resolved_host = host or (prof.base_url if prof else None)
    resolved_model = default_model or (prof.model if prof else None)
    resolved_timeout = timeout if timeout is not None else (prof.timeout if prof else None)

    if resolved_host is not None:
        init_kwargs.setdefault("host", resolved_host)
    if resolved_model is not None:
        init_kwargs.setdefault("default_model", resolved_model)
    if resolved_timeout is not None:
        init_kwargs.setdefault("timeout", resolved_timeout)

    return cls(**init_kwargs)  # type: ignore[call-arg]


def provider_from_profile(profile_name: str = "edge-default") -> LLMProvider:
    """Convenience: profile name → live provider."""
    prof = get_profile(profile_name)
    return get_provider(
        prof.provider,
        profile=prof,
    )
