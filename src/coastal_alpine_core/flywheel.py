"""
Data Flywheel - Full integration ready version

Includes convenience methods for easy integration into portals.
"""

import json
import logging
import time
import uuid
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

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
