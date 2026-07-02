import functools
import json
import logging
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

try:
    import psutil  # Optional for real system metrics
except ImportError:
    psutil = None  # type: ignore

logger = logging.getLogger("CoastalAlpineCore.Telemetry")


class TelemetryTracker:
    """
    Enterprise-grade synchronous telemetry for edge AI systems.
    Tracks latency, tokens, estimated + optional real power/system metrics.
    Supports data flywheel input and Bayesian optimisation loops.
    """

    DEFAULT_BASE_POWER = {"RPi5": 8.0, "default": 5.0}
    DEFAULT_NPU_POWER = 2.5

    @staticmethod
    def measure_latency(action_name: str) -> dict[str, Any]:
        return {"action": action_name, "start": time.perf_counter()}

    @staticmethod
    def _get_system_metrics() -> dict[str, Any]:
        if psutil is None:
            return {}
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage_percent": psutil.disk_usage("/").percent,
            }
        except Exception:
            return {}

    @staticmethod
    def complete_measurement(
        measurement: dict[str, Any],
        token_count: int = 0,
        device: str = "RPi5",
        base_power: dict[str, float] | None = None,
        include_system_metrics: bool = False,
    ) -> dict[str, Any]:
        duration = time.perf_counter() - measurement["start"]
        tokens_per_sec = (token_count / duration) if token_count > 0 and duration > 0 else 0.0

        powers = base_power or TelemetryTracker.DEFAULT_BASE_POWER
        base = powers.get(device, powers.get("default", 5.0))
        npu_add = (
            TelemetryTracker.DEFAULT_NPU_POWER
            if "NPU" in device or "hailo" in device.lower()
            else 0.0
        )
        active_power = base + npu_add
        energy_joules = active_power * duration

        results: dict[str, Any] = {
            "action": measurement["action"],
            "duration_seconds": round(duration, 4),
            "tokens_processed": token_count,
            "tokens_per_second": round(tokens_per_sec, 2),
            "estimated_power_watts": round(active_power, 2),
            "estimated_energy_joules": round(energy_joules, 4),
            "hardware_device": device,
        }

        if include_system_metrics:
            results.update(TelemetryTracker._get_system_metrics())

        # Structured logging for better observability and flywheel input
        logger.info(json.dumps({"telemetry": results}, default=str))
        return results

    @staticmethod
    @contextmanager
    def track(
        action_name: str, device: str = "RPi5", include_system_metrics: bool = False
    ) -> Generator[dict[str, Any], None, None]:
        measurement = TelemetryTracker.measure_latency(action_name)
        try:
            yield measurement
        finally:
            TelemetryTracker.complete_measurement(
                measurement, device=device, include_system_metrics=include_system_metrics
            )


def log_performance(action_name: str, device: str = "RPi5"):
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            measurement = TelemetryTracker.measure_latency(action_name)
            result = func(*args, **kwargs)
            token_count = 0
            if isinstance(result, str):
                token_count = len(result.split())
            elif isinstance(result, dict):
                token_count = len(str(result).split())
            TelemetryTracker.complete_measurement(
                measurement, token_count=token_count, device=device
            )
            return result

        return wrapper

    return decorator
