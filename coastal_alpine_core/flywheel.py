"""
Data Flywheel Scaffolding + Bayesian Optimisation Hooks (Enhanced)

Now includes:
- Human-in-the-Loop (HITL) feedback updates
- Evaluation loop (rule-based + LLM-as-judge scaffolding)
- Helpers for automatic recording after hardware enforcement
"""

import json
import logging
import time
import uuid
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

logger = logging.getLogger("CoastalAlpineCore.Flywheel")


@dataclass
class Trajectory:
    trajectory_id: str
    timestamp: str
    action: str
    input_summary: str
    output_summary: str
    outcome: str  # success, failure, human_corrected, timeout, pending_review
    latency_seconds: float
    estimated_energy_joules: float
    system_metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    human_feedback: Optional[str] = None
    quality_score: Optional[float] = None   # 0.0 - 1.0 from evaluation loop


class DataFlywheel:
    def __init__(self, storage_path: str = "flywheel_trajectories.jsonl"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def record_trajectory(self, trajectory: Trajectory) -> None:
        with self.storage_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(trajectory), default=str) + "\n")
        logger.info(f"Flywheel: Recorded {trajectory.trajectory_id} ({trajectory.outcome})")

    def update_trajectory_with_feedback(self, trajectory_id: str, human_feedback: str, new_outcome: str = "human_corrected") -> bool:
        """Update an existing trajectory with human feedback (HITL)."""
        correction = Trajectory(
            trajectory_id=f"correction-{trajectory_id}",
            timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            action="human_feedback",
            input_summary=f"Feedback on {trajectory_id}",
            output_summary=human_feedback,
            outcome=new_outcome,
            latency_seconds=0.0,
            estimated_energy_joules=0.0,
            metadata={"original_trajectory_id": trajectory_id}
        )
        self.record_trajectory(correction)
        logger.info(f"Flywheel: Human feedback recorded for {trajectory_id}")
        return True

    def get_recent_trajectories(self, limit: int = 100) -> List[Trajectory]:
        trajectories = []
        if not self.storage_path.exists():
            return trajectories
        with self.storage_path.open("r", encoding="utf-8") as f:
            for line in f.readlines()[-limit:]:
                try:
                    data = json.loads(line.strip())
                    trajectories.append(Trajectory(**data))
                except Exception:
                    continue
        return trajectories

    def curate_golden_set(self, min_quality: float = 0.7) -> List[Trajectory]:
        all_traj = self.get_recent_trajectories(limit=500)
        golden = [t for t in all_traj if (t.quality_score or 0.0) >= min_quality or t.outcome in ("success", "human_corrected")]
        return golden

    def evaluate_trajectory(self, trajectory: Trajectory, llm_judge_func: Optional[Callable[[str], float]] = None) -> float:
        """
        Evaluation loop: Assigns a quality score.
        - Rule-based by default
        - Optional LLM-as-judge via injected function
        """
        score = 0.5
        if trajectory.outcome == "success":
            score += 0.3
        elif trajectory.outcome == "human_corrected":
            score += 0.2
        elif trajectory.outcome in ("failure", "timeout"):
            score -= 0.2
        if trajectory.metadata.get("requires_human_review") is False:
            score += 0.1

        if llm_judge_func and trajectory.output_summary:
            try:
                llm_score = llm_judge_func(trajectory.output_summary)
                score = (score + llm_score) / 2
            except Exception:
                pass

        trajectory.quality_score = max(0.0, min(1.0, score))
        return trajectory.quality_score


class BayesianOptimisationHook:
    def __init__(self):
        self.history: List[Dict[str, Any]] = []

    def suggest_next_configuration(self, current_metrics: Dict[str, float]) -> Dict[str, Any]:
        logger.info("BayesianOptimisationHook: suggest_next_configuration called (placeholder)")
        return {
            "suggested_reporting_interval_minutes": 5,
            "suggested_model_temperature": 0.3,
            "reason": "Placeholder suggestion"
        }

    def update_with_observation(self, config: Dict[str, Any], observed_metrics: Dict[str, float]) -> None:
        self.history.append({"config": config, "metrics": observed_metrics, "timestamp": time.time()})
        logger.info("BayesianOptimisationHook: Recorded new observation")


# Convenience helper for portals after hardware enforcement
def record_hardware_outcome(
    flywheel: DataFlywheel,
    plan_id: str,
    action: str,
    success: bool,
    latency_seconds: float = 0.0,
    energy_joules: float = 0.0,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Helper to automatically record outcome after hardware enforcement (irrigation, aeration, etc.)."""
    outcome = "success" if success else "failure"
    traj = Trajectory(
        trajectory_id=str(uuid.uuid4()),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        action=f"hardware_enforcement_{action}",
        input_summary=f"Plan {plan_id}",
        output_summary=f"Hardware action {action} executed",
        outcome=outcome,
        latency_seconds=latency_seconds,
        estimated_energy_joules=energy_joules,
        metadata=metadata or {"plan_id": plan_id}
    )
    flywheel.record_trajectory(traj)
