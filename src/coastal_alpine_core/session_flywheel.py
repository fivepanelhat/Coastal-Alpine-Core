"""
Bridge SessionEvent sessions to DataFlywheel Trajectory records (Sprint C).

SessionEvent = fine-grained HITL evidence stream.
Trajectory  = outcome-level flywheel sample for eval / golden-set curation.

CAT: local-first JSONL, no secrets in summaries, optional soft use by Weaver/Aether.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

from coastal_alpine_core.telemetry import DataFlywheel, Trajectory


def record_session_trajectory(
    *,
    session_id: str,
    action: str,
    outcome: str,
    input_summary: str = "",
    output_summary: str = "",
    latency_seconds: float = 0.0,
    estimated_energy_joules: float = 0.0,
    tenant_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    storage_path: str | Path | None = None,
    flywheel: DataFlywheel | None = None,
) -> Trajectory:
    """
    Append one outcome-level Trajectory for a completed (or failed) session.

    Summaries must stay free of secrets / raw PII — callers pass lengths and
    status codes, not prompt bodies or credentials.
    """
    wheel = flywheel or DataFlywheel(
        storage_path=str(storage_path or "flywheel_trajectories.jsonl")
    )
    meta = dict(metadata or {})
    meta.setdefault("session_id", session_id)
    if tenant_id is not None:
        meta.setdefault("tenant_id", tenant_id)

    traj = Trajectory(
        trajectory_id=str(uuid.uuid4()),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        action=action,
        input_summary=(input_summary or "")[:500],
        output_summary=(output_summary or "")[:500],
        outcome=outcome,
        latency_seconds=float(latency_seconds or 0.0),
        estimated_energy_joules=float(estimated_energy_joules or 0.0),
        metadata=meta,
    )
    wheel.record_trajectory(traj)
    return traj
