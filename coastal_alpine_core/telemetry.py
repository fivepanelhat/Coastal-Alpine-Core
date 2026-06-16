import time
import functools
import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, Generator, Optional

logger = logging.getLogger("CoastalAlpineCore.Telemetry")


class TelemetryTracker:
    """
    Performance and hardware energy-efficiency tracker for edge-native devices.
    Supports the global optimisation objective (latency L + power P).
    Can be extended with real hardware sensors and Bayesian Optimisation input.
    """

    DEFAULT_BASE_POWER = {"RPi5": 8.0, "default": 5.0}
    DEFAULT_NPU_POWER = 2.5

    @staticmethod
    def measure_latency(action_name: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        return {"action": action_name, "start": start_time}

    @staticmethod
    def complete_measurement(
        measurement: Dict[str, Any],
        token_count: int = 0,
        device: str = "RPi5",
        base_power: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        duration = time.perf_counter() - measurement["start"]
        tokens_per_sec = (token_count / duration) if token_count > 0 and duration > 0 else 0.0

        powers = base_power or TelemetryTracker.DEFAULT_BASE_POWER
        base = powers.get(device, powers.get("default", 5.0))
        npu_add = TelemetryTracker.DEFAULT_NPU_POWER if "NPU" in device or "hailo" in device.lower() else 0.0
        active_power = base + npu_add
        energy_joules = active_power * duration

        results: Dict[str, Any] = {
            "action": measurement["action"],
            "duration_seconds": round(duration, 4),
            "tokens_processed": token_count,
            "tokens_per_second": round(tokens_per_sec, 2),
            "estimated_power_watts": round(active_power, 2),
            "estimated_energy_joules": round(energy_joules, 4),
            "hardware_device": device,
        }

        logger.info(
            f"Edge Telemetry | {results['action']}: {results['duration_seconds']}s | "
            f"{results['tokens_per_second']} t/s | {results['estimated_energy_joules']} J on {device}"
        )
        return results

    @staticmethod
    @contextmanager
    def track(action_name: str, device: str = "RPi5") -> Generator[Dict[str, Any], None, None]:
        """Context manager for clean measurement blocks."""
        measurement = TelemetryTracker.measure_latency(action_name)
        try:
            yield measurement
        finally:
            TelemetryTracker.complete_measurement(measurement, device=device)


def log_performance(action_name: str, device: str = "RPi5"):
    """Decorator for automatic telemetry on sync functions."""

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

            TelemetryTracker.complete_measurement(measurement, token_count=token_count, device=device)
            return result

        return wrapper

    return decorator
