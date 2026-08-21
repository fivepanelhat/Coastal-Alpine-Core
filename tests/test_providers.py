"""Sprint A Phase 2 — provider seams smoke tests."""

from coastal_alpine_core import (
    LLMProvider,
    ProviderProfile,
    SovereignOllamaClient,
    get_profile,
    get_provider,
    list_providers,
    provider_from_profile,
)
from coastal_alpine_core.providers import PROFILES


def test_list_providers_includes_ollama():
    assert "ollama" in list_providers()


def test_get_profile_edge_default():
    p = get_profile("edge-default")
    assert isinstance(p, ProviderProfile)
    assert p.provider == "ollama"
    assert p.base_url.startswith("http")


def test_unknown_profile_raises():
    try:
        get_profile("not-a-real-profile")
        assert False, "expected KeyError"
    except KeyError:
        pass


def test_get_provider_returns_sovereign_client():
    client = get_provider("ollama", profile="edge-fast")
    assert isinstance(client, SovereignOllamaClient)
    assert isinstance(client, LLMProvider)
    assert client.default_model  # set from profile


def test_provider_from_profile():
    client = provider_from_profile("edge-coder")
    assert isinstance(client, SovereignOllamaClient)
    assert "coder" in client.default_model or client.default_model.startswith("qwen")


def test_builtin_profiles_cover_edge():
    assert "edge-default" in PROFILES
    assert "edge-fast" in PROFILES
    assert "edge-coder" in PROFILES
