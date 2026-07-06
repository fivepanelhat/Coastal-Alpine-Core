import logging
import time
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


class SovereignOllamaClient:
    """
    Robust synchronous connection wrapper for local offline Ollama SLM deployments.
    Handles network dropouts and model loads with automated retries and exponential backoff.
    Falls back to local deterministic responses when fully disconnected.

    Integrates with TelemetryTracker for latency and energy measurement (Phase 1 optimisation).
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        default_model: str = "gemma4:e4b",
    ):
        self.host = host.rstrip("/")
        self.default_model = default_model
        # Keep-alive session: repeated generate() calls reuse one TCP
        # connection instead of a fresh handshake per request.
        self.session = requests.Session()

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
        Integrates TelemetryTracker for latency/power metrics (supports Bayesian Optimisation loop).
        """
        from coastal_alpine_core.telemetry import TelemetryTracker

        active_model = model or self.default_model
        url = f"{self.host}/api/generate"
        payload: GeneratePayload = {
            "model": active_model,
            "prompt": prompt,
            "stream": False,
        }
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        measurement = TelemetryTracker.measure_latency("ollama_generate")

        for attempt in range(retries):
            try:
                response = self.session.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    result: OllamaResponse = response.json()
                    token_count = result.get("eval_count", len(prompt.split()))
                    TelemetryTracker.complete_measurement(measurement, token_count=token_count)
                    return result
                else:
                    logger.warning(
                        f"Ollama returned status {response.status_code}. Attempt {attempt + 1}/{retries}"
                    )
            except requests.RequestException as e:
                logger.warning(
                    f"Failed connecting to local Ollama on attempt {attempt + 1}/{retries}: {e}"
                )

            if attempt < retries - 1:
                sleep_time = backoff * (2**attempt)
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)

        logger.error(
            "All local Ollama retries exhausted. Providing local deterministic fallback response."
        )
        fallback = self._fallback_response(prompt, active_model)
        TelemetryTracker.complete_measurement(measurement, token_count=len(prompt.split()))
        return fallback

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
