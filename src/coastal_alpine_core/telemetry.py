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
 import psutil # Optional for real system metrics
except ImportError:
 psutil = None # type: ignore

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
 # interval=None is non-blocking (uses last sample) - critical on edge loops
 return {
 "cpu_percent": psutil.cpu_percent(interval=None),
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
 try:
 result = func(*args, **kwargs)
 except Exception:
 # Still close the measurement: failed calls are exactly the
 # latency samples the flywheel needs for anomaly detection.
 TelemetryTracker.complete_measurement(
 measurement, token_count=0, device=device
 )
 raise
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
 _instances: dict[str, "DataFlywheel"] = {} # Simple tenant-aware singleton

 # SD-card safety defaults (overridable per instance)
 DEFAULT_MAX_BYTES = 5 * 1024 * 1024
 DEFAULT_KEEP_LINES = 2000

 def __new__(cls, storage_path: str = "flywheel_trajectories.jsonl", **kwargs):
 if storage_path not in cls._instances:
 cls._instances[storage_path] = super().__new__(cls)
 return cls._instances[storage_path]

 def __init__(
 self,
 storage_path: str = "flywheel_trajectories.jsonl",
 max_bytes: int | None = None,
 keep_lines: int | None = None,
 ):
 if hasattr(self, "_initialized"):
 return
 self.storage_path = Path(storage_path)
 self.storage_path.parent.mkdir(parents=True, exist_ok=True)
 self.max_bytes = max_bytes if max_bytes is not None else self.DEFAULT_MAX_BYTES
 self.keep_lines = (
 keep_lines if keep_lines is not None else self.DEFAULT_KEEP_LINES
 )
 self._initialized = True

 def record_trajectory(self, trajectory: Trajectory) -> None:
 with self.storage_path.open("a", encoding="utf-8") as f:
 f.write(json.dumps(asdict(trajectory), default=str) + "\n")
 logger.info(
 "Flywheel: Recorded %s (%s)", trajectory.trajectory_id, trajectory.outcome
 )
 self.rotate_if_needed()

 def rotate_if_needed(self) -> bool:
 """Trim JSONL when over max_bytes. Returns True if rotated."""
 try:
 if not self.storage_path.is_file():
 return False
 if self.storage_path.stat().st_size <= self.max_bytes:
 return False
 lines = self.storage_path.read_text(
 encoding="utf-8", errors="replace"
 ).splitlines()
 if len(lines) > self.keep_lines:
 kept = lines[-self.keep_lines :]
 self.storage_path.write_text(
 "\n".join(kept) + "\n", encoding="utf-8"
 )
 else:
 data = self.storage_path.read_bytes()
 self.storage_path.write_bytes(data[-(self.max_bytes // 2) :])
 logger.warning("Flywheel rotated at %s", self.storage_path)
 return True
 except OSError as e:
 logger.error("Flywheel rotation failed: %s", e)
 return False

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

 def update_trajectory_with_feedback(
 self, trajectory_id: str, feedback: str, new_outcome: str = "human_corrected"
 ) -> bool:
 """Rewrite the matching record with human feedback attached."""
 trajectories = self._load_all()
 updated = False
 for traj in trajectories:
 if traj.trajectory_id == trajectory_id:
 traj.human_feedback = feedback
 traj.outcome = new_outcome
 updated = True
 break

 if not updated:
 logger.warning(f"Flywheel: trajectory {trajectory_id} not found for feedback update")
 return False

 tmp_path = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
 with tmp_path.open("w", encoding="utf-8") as f:
 for traj in trajectories:
 f.write(json.dumps(asdict(traj), default=str) + "\n")
 tmp_path.replace(self.storage_path)
 logger.info(f"Flywheel: attached human feedback to {trajectory_id}")
 return True

 def _load_all(self) -> list[Trajectory]:
 """Parse every valid JSONL record; corrupt lines are skipped, never fatal."""
 if not self.storage_path.exists():
 return []
 trajectories: list[Trajectory] = []
 valid_fields = {f.name for f in Trajectory.__dataclass_fields__.values()}
 with self.storage_path.open("r", encoding="utf-8") as f:
 for line_no, line in enumerate(f, start=1):
 line = line.strip()
 if not line:
 continue
 try:
 data = json.loads(line)
 trajectories.append(
 Trajectory(**{k: v for k, v in data.items() if k in valid_fields})
 )
 except (json.JSONDecodeError, TypeError) as e:
 logger.warning(f"Flywheel: skipping corrupt line {line_no}: {e}")
 return trajectories

 def get_recent_trajectories(self, limit: int = 100) -> list[Trajectory]:
 """Return the last *limit* trajectories (loads file; use modest limits on edge)."""
 if limit <= 0:
 return []
 # Fast path: for small limits, read from end of file when possible
 if not self.storage_path.exists():
 return []
 try:
 # Read last ~256KB for recent windows - avoids full scan on large flywheels
 size = self.storage_path.stat().st_size
 if size > 256 * 1024 and limit <= 100:
 with self.storage_path.open("rb") as f:
 f.seek(max(0, size - 256 * 1024))
 chunk = f.read().decode("utf-8", errors="replace")
 # Drop partial first line
 lines = chunk.splitlines()[1:]
 valid_fields = {fld.name for fld in Trajectory.__dataclass_fields__.values()}
 recent: list[Trajectory] = []
 for line in lines:
 line = line.strip()
 if not line:
 continue
 try:
 data = json.loads(line)
 recent.append(
 Trajectory(
 **{k: v for k, v in data.items() if k in valid_fields}
 )
 )
 except (json.JSONDecodeError, TypeError):
 continue
 return recent[-limit:]
 except OSError:
 pass
 return self._load_all()[-limit:]

 def curate_golden_set(self, min_quality: float = 0.7) -> list[Trajectory]:
 """High-quality successful trajectories suitable for fine-tuning input."""
 return [
 t
 for t in self._load_all()
 if t.outcome == "success" and t.quality_score is not None and t.quality_score >= min_quality
 ]

 def evaluate_trajectory(
 self, trajectory: Trajectory, llm_judge_func: Callable | None = None
 ) -> float:
 """Score a trajectory 0.0-1.0 via the supplied judge, else a heuristic."""
 if llm_judge_func is not None:
 score = float(llm_judge_func(trajectory))
 else:
 base = {"success": 0.8, "human_corrected": 0.5}.get(trajectory.outcome, 0.2)
 # Fast responses are worth slightly more on constrained edge hardware
 if trajectory.latency_seconds and trajectory.latency_seconds < 1.0:
 base += 0.1
 if trajectory.human_feedback:
 base += 0.1
 score = base
 trajectory.quality_score = max(0.0, min(1.0, score))
 return trajectory.quality_score
