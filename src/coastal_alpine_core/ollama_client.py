"""Sovereign Ollama client — edge-friendly, keep-alive, retries, offline fallback."""

from __future__ import annotations

import contextlib
import hashlib
import logging
import time
from collections import OrderedDict
from typing import Any, TypedDict

import requests

logger = logging.getLogger("CoastalAlpineCore.SovereignOllamaClient")


class GeneratePayload(TypedDict, total=False):
    model: str
    prompt: str
    stream: bool
    system: str
    options: dict[str, Any]


class OllamaResponse(TypedDict, total=False):
    model: str
    created_at: str
    response: str
    done: bool
    context: list[int]
    total_duration: int
    load_duration: int
    prompt_eval_count: int
    eval_count: int


class _LRUCache:
    """Tiny in-process response cache for identical generate prompts."""

    def __init__(self, maxsize: int = 32):
        self.maxsize = maxsize
        self._data: OrderedDict[str, OllamaResponse] = OrderedDict()

    def get(self, key: str) -> OllamaResponse | None:
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def set(self, key: str, value: OllamaResponse) -> None:
        if key in self._data:
            self._data.move_to_end(key)
        self._data[key] = value
        while len(self._data) > self.maxsize:
            self._data.popitem(last=False)


class SovereignOllamaClient:
    """
    Robust synchronous connection wrapper for local offline Ollama SLM deployments.
    Handles network dropouts and model loads with automated retries and exponential backoff.
    Falls back to local deterministic responses when fully disconnected.
    """

    # Edge-friendly default generation options (short answers for control loops)
    DEFAULT_OPTIONS: dict[str, Any] = {
        "temperature": 0.2,
        "num_predict": 256,
    }

    def __init__(
        self,
        host: str = "http://localhost:11434",
        default_model: str = "gemma4:e4b",
        timeout: float = 30.0,
        cache_size: int = 32,
        enable_cache: bool = True,
    ):
        self.host = host.rstrip("/")
        self.default_model = default_model
        self.timeout = timeout
        self.session = requests.Session()
        self._cache = _LRUCache(cache_size) if enable_cache and cache_size > 0 else None

    def close(self) -> None:
        with contextlib.suppress(Exception):
            self.session.close()

    def check_health(self) -> bool:
        """Checks if the local Ollama server is responsive."""
        try:
            response = self.session.get(f"{self.host}/api/tags", timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def list(self) -> dict[str, Any]:
        """Return the installed model listing ({"models": [...]}, ollama-py parity)."""
        response = self.session.get(f"{self.host}/api/tags", timeout=5)
        response.raise_for_status()
        return response.json()

    def _cache_key(
        self, prompt: str, model: str, system: str | None, options: dict[str, Any] | None
    ) -> str:
        raw = f"{model}|{system or ''}|{options or {}}|{prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        system: str | None = None,
        options: dict[str, Any] | None = None,
        retries: int = 3,
        backoff: float = 1.0,
    ) -> OllamaResponse:
        """
        Generates completion with exponential backoff retry.
        Integrates TelemetryTracker for latency/power metrics.
        """
        from coastal_alpine_core.telemetry import TelemetryTracker

        active_model = model or self.default_model
        merged_options = {**self.DEFAULT_OPTIONS, **(options or {})}
        url = f"{self.host}/api/generate"
        payload: GeneratePayload = {
            "model": active_model,
            "prompt": prompt,
            "stream": False,
            "options": merged_options,
        }
        if system:
            payload["system"] = system

        if self._cache is not None:
            key = self._cache_key(prompt, active_model, system, merged_options)
            cached = self._cache.get(key)
            if cached is not None:
                logger.debug("Ollama cache hit for model=%s", active_model)
                return cached
        else:
            key = ""

        measurement = TelemetryTracker.measure_latency("ollama_generate")

        for attempt in range(retries):
            try:
                response = self.session.post(url, json=payload, timeout=self.timeout)
                if response.status_code == 200:
                    result: OllamaResponse = response.json()
                    token_count = result.get("eval_count", len(prompt.split()))
                    TelemetryTracker.complete_measurement(
                        measurement, token_count=token_count
                    )
                    if self._cache is not None and key:
                        self._cache.set(key, result)
                    return result
                logger.warning(
                    "Ollama returned status %s. Attempt %s/%s",
                    response.status_code,
                    attempt + 1,
                    retries,
                )
            except requests.RequestException as e:
                logger.warning(
                    "Failed connecting to local Ollama on attempt %s/%s: %s",
                    attempt + 1,
                    retries,
                    e,
                )

            if attempt < retries - 1:
                sleep_time = backoff * (2**attempt)
                logger.info("Retrying in %s seconds...", sleep_time)
                time.sleep(sleep_time)

        logger.error(
            "All local Ollama retries exhausted. Providing local deterministic fallback response."
        )
        fallback = self._fallback_response(prompt, active_model)
        TelemetryTracker.complete_measurement(
            measurement, token_count=len(prompt.split())
        )
        return fallback

    # ---- aliases used by Weaver / portals ----

    def invoke(self, prompt: str, **kwargs: Any) -> str:
        """Return plain text completion (chat-style API)."""
        result = self.generate(prompt, **kwargs)
        return str(result.get("response", ""))

    def chat(self, prompt: str, **kwargs: Any) -> str:
        return self.invoke(prompt, **kwargs)

    def _fallback_response(self, prompt: str, model: str) -> OllamaResponse:
        """
        Deterministic fallback for testing / full offline mode. Never actuates hardware.
        """
        fallback_text = (
            f"[OFFLINE MOCK RESPONSE - Model: {model}]\n"
            f"Edge system operating in disconnected fallback mode.\n"
            f"Prompt received (truncated): {prompt[:120]}...\n"
            f"Execution completed successfully (no physical hardware actuated)."
        )
        return {
            "model": model,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "response": fallback_text,
            "done": True,
            "context": [0],
            "total_duration": 1000000,
            "load_duration": 10000,
            "prompt_eval_count": len(prompt.split()),
            "eval_count": len(fallback_text.split()),
        }
