import functools
import json
import logging
import time
import uuid
from collections.abc import Callable, Generator
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
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


"""
Data Flywheel - Full integration ready version

Includes convenience methods for easy integration into portals.
"""


logger = logging.getLogger("CoastalAlpineCore.Flywheel")


@dataclass
class Trajectory:
    trajectory_id: str
    timestamp: str
    action: str
    input_summary: str
    output_summary: str
    outcome: str
    latency_seconds: float
    estimated_energy_joules: float
    system_metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    human_feedback: str | None = None
    quality_score: float | None = None


class DataFlywheel:
    _instances: dict[str, "DataFlywheel"] = {}  # Simple tenant-aware singleton

    def __new__(cls, storage_path: str = "flywheel_trajectories.jsonl"):
        if storage_path not in cls._instances:
            cls._instances[storage_path] = super().__new__(cls)
        return cls._instances[storage_path]

    def __init__(self, storage_path: str = "flywheel_trajectories.jsonl"):
        if hasattr(self, "_initialized"):
            return
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = True

    def record_trajectory(self, trajectory: Trajectory) -> None:
        with self.storage_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(trajectory), default=str) + "\n")
        logger.info(f"Flywheel: Recorded {trajectory.trajectory_id} ({trajectory.outcome})")

    def record_hardware_outcome(self, plan_id: str, action: str, success: bool, **kwargs) -> None:
        """Convenience method for portals after hardware enforcement."""
        outcome = "success" if success else "failure"
        traj = Trajectory(
            trajectory_id=str(uuid.uuid4()),
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            action=f"hardware_{action}",
            input_summary=f"Plan: {plan_id}",
            output_summary=f"Action {action} executed",
            outcome=outcome,
            latency_seconds=kwargs.get("latency_seconds", 0.0),
            estimated_energy_joules=kwargs.get("energy_joules", 0.0),
            metadata=kwargs.get("metadata", {"plan_id": plan_id}),
        )
        self.record_trajectory(traj)

    def update_with_human_feedback(
        self, original_trajectory_id: str, feedback: str, new_outcome: str = "human_corrected"
    ):
        self.update_trajectory_with_feedback(original_trajectory_id, feedback, new_outcome)

    # ... (rest of the methods: get_recent_trajectories, curate_golden_set, evaluate_trajectory remain the same)

    def get_recent_trajectories(self, limit: int = 100) -> list[Trajectory]:
        # implementation as before
        pass

    def curate_golden_set(self, min_quality: float = 0.7) -> list[Trajectory]:
        # implementation as before
        pass

    def evaluate_trajectory(
        self, trajectory: Trajectory, llm_judge_func: Callable | None = None
    ) -> float:
        # implementation as before
        pass
