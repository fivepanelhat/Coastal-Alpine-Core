"""Sprint C — session outcome → Trajectory."""

from coastal_alpine_core import DataFlywheel, record_session_trajectory


def test_record_session_trajectory(tmp_path):
    path = tmp_path / "flywheel.jsonl"
    wheel = DataFlywheel(storage_path=str(path))
    traj = record_session_trajectory(
        session_id="s-1",
        action="weaver.process_message",
        outcome="success",
        input_summary="chars=12",
        output_summary="status=ok",
        latency_seconds=0.05,
        tenant_id="t-1",
        flywheel=wheel,
    )
    assert traj.trajectory_id
    assert traj.metadata.get("session_id") == "s-1"
    assert traj.metadata.get("tenant_id") == "t-1"
    recent = wheel.get_recent_trajectories(limit=5)
    assert any(t.trajectory_id == traj.trajectory_id for t in recent)
