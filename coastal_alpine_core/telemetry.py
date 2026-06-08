import time
import functools
import logging
from typing import Dict, Any, Callable

# Configure default logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("CoastalAlpineCore.Telemetry")

class TelemetryTracker:
    """
    Performance and hardware energy-efficiency tracker designed for edge-native devices.
    """

    @staticmethod
    def measure_latency(action_name: str) -> Dict[str, Any]:
        """
        Simple context manager-like return or helper to measure duration of edge operations.
        """
        start_time = time.perf_counter()
        return {
            "action": action_name,
            "start": start_time
        }

    @staticmethod
    def complete_measurement(measurement: Dict[str, Any], token_count: int = 0, device: str = "RPi5") -> Dict[str, Any]:
        """
        Calculates performance and energy characteristics.
        """
        duration = time.perf_counter() - measurement["start"]
        tokens_per_sec = (token_count / duration) if token_count > 0 and duration > 0 else 0.0
        
        # Estimate power consumption (Watts * hours) based on theoretical edge performance:
        # RPi 5 peak under load is ~8-10W. Hailo-10L NPU peak is ~2.5W.
        base_power = 8.0 if device == "RPi5" else 5.0
        active_power = base_power + (2.5 if "NPU" in device or "hailo" in device.lower() else 1.5)
        energy_used_joules = active_power * duration
        
        results = {
            "action": measurement["action"],
            "duration_seconds": round(duration, 4),
            "tokens_processed": token_count,
            "tokens_per_second": round(tokens_per_sec, 2),
            "estimated_power_watts": active_power,
            "estimated_energy_joules": round(energy_used_joules, 4),
            "hardware_device": device
        }
        
        logger.info(
            f"Edge Telemetry - {results['action']} finished. "
            f"Time: {results['duration_seconds']}s, "
            f"Speed: {results['tokens_per_second']} t/s, "
            f"Energy: {results['estimated_energy_joules']} J on {device}"
        )
        return results

def log_performance(action_name: str, device: str = "RPi5"):
    """
    Decorator to easily log timing and power performance metrics of python functions.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            measurement = TelemetryTracker.measure_latency(action_name)
            result = func(*args, **kwargs)
            # Try to estimate tokens if the function output is a string or returns token info
            token_count = 0
            if isinstance(result, str):
                token_count = len(result.split())  # simple word count fallback
            elif isinstance(result, dict) and "text" in result:
                token_count = len(result["text"].split())
                
            TelemetryTracker.complete_measurement(measurement, token_count=token_count, device=device)
            return result
        return wrapper
    return decorator
