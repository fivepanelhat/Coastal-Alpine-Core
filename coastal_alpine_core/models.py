import time
import logging
from typing import Dict, Any, Optional, TypedDict


class GeneratePayload(TypedDict, total=False):
    model: str
    prompt: str
    stream: bool
    system: str
    options: Dict[str, Any]


import requests  # type: ignore

logger = logging.getLogger("CoastalAlpineCore.OllamaClient")


class SovereignOllamaClient:
    """
    Robust connection wrapper for local offline Ollama SLM deployments.
    Handles network dropouts and model loads with automated retries.
    """

    def __init__(
        self,
        host: str = "http://localhost:11434",
        default_model: str = "gemma4:e4b",
    ):
        self.host = host.rstrip("/")
        self.default_model = default_model

    def check_health(self) -> bool:
        """Checks if the local Ollama server is responsive."""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=3)
            return response.status_code == 200
        except Exception:
            return False

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        retries: int = 3,
        backoff: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Generates completion with exponential backoff retry. Falls back to mock responses if completely offline.
        """
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

        for attempt in range(retries):
            try:
                response = requests.post(url, json=payload, timeout=30)
                if response.status_code == 200:
                    return response.json()
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
        return self._fallback_response(prompt, active_model)

    def _fallback_response(self, prompt: str, model: str) -> Dict[str, Any]:
        """
        Mock fallback for testing when Ollama server is unavailable.
        """
        fallback_text = (
            f"[OFFLINE MOCK RESPONSE - Model: {model}]\n"
            f"Edge system is operating in disconnected fallback mode.\n"
            f"Prompt received: {prompt[:100]}...\n"
            f"Execution completed successfully. (No physical hardware was actuated)."
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
