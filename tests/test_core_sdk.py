"""Smoke suite for the core SDK — the release gate runs this."""

import asyncio
from unittest.mock import MagicMock, patch

from coastal_alpine_core import DataFlywheel, Trajectory
from coastal_alpine_core.portal_core.ai_agent import AIAgent
from coastal_alpine_core.portal_core.av_capture import AVCapture


def _make_flywheel(tmp_path):
    return DataFlywheel(storage_path=str(tmp_path / "flywheel.jsonl"))


class TestDataFlywheel:
    def test_record_and_read_back(self, tmp_path):
        fw = _make_flywheel(tmp_path)
        fw.record_hardware_outcome("plan-1", "pump_on", True)
        recent = fw.get_recent_trajectories()
        assert len(recent) == 1
        assert recent[0].outcome == "success"

    def test_human_feedback_roundtrip(self, tmp_path):
        fw = _make_flywheel(tmp_path)
        fw.record_hardware_outcome("plan-2", "valve_open", False)
        tid = fw.get_recent_trajectories()[0].trajectory_id

        assert fw.update_trajectory_with_feedback(tid, "operator confirmed fault")
        updated = fw.get_recent_trajectories()[0]
        assert updated.human_feedback == "operator confirmed fault"
        assert updated.outcome == "human_corrected"

    def test_feedback_on_unknown_id_is_noop(self, tmp_path):
        fw = _make_flywheel(tmp_path)
        assert fw.update_trajectory_with_feedback("missing", "x") is False

    def test_evaluate_and_curate_golden_set(self, tmp_path):
        fw = _make_flywheel(tmp_path)
        fw.record_hardware_outcome("plan-3", "aerator_boost", True, latency_seconds=0.5)
        traj = fw.get_recent_trajectories()[0]
        score = fw.evaluate_trajectory(traj)
        assert 0.0 <= score <= 1.0

        golden = [Trajectory(**{**traj.__dict__})]
        assert golden[0].quality_score == score


class TestAIAgent:
    def _agent(self):
        return AIAgent(ollama_host="http://localhost:11434", model="gemma4:e4b")

    def test_default_plan_is_safe(self):
        plan = self._agent()._generate_default_plan()
        assert "opt-default-" in plan["plan_id"]
        assert plan["pump_action"] == "medium"
        assert plan["requires_human_review"] is True

    def test_plan_rejects_unsupported_actuation(self):
        agent = self._agent()
        response = {"response": '{"plan_id":"opt-x", "pump_action":"super_high"}'}
        with patch.object(agent.client, "generate", return_value=response):
            plan = asyncio.run(agent.generate_optimization_plan({}, {}, {}))
        assert "opt-default-" in plan["plan_id"]

    def test_plan_keeps_actions_at_top_level(self):
        agent = self._agent()
        response = {
            "response": '{"plan_id":"opt-1", "pump_action":"medium", "confidence_score":0.9}'
        }
        with patch.object(agent.client, "generate", return_value=response):
            plan = asyncio.run(agent.generate_optimization_plan({}, {}, {}))
        assert plan["pump_action"] == "medium"
        assert plan["actions"]["pump_action"] == "medium"

    def test_health_check_requires_model_loaded(self):
        agent = self._agent()
        with patch.object(
            agent.client, "list", return_value={"models": [{"name": "other:latest"}]}
        ):
            assert asyncio.run(agent.health_check()) is False
        with patch.object(
            agent.client, "list", return_value={"models": [{"name": "gemma4:e4b"}]}
        ):
            assert asyncio.run(agent.health_check()) is True


class TestAVCapture:
    def test_uninitialised_is_healthy_degraded(self):
        av = AVCapture()
        assert asyncio.run(av.health_check()) is True

    def test_unhealthy_when_all_streams_down(self):
        av = AVCapture()
        cap = MagicMock()
        cap.isOpened.return_value = False
        av.video_capture = cap
        stream = MagicMock()
        stream.is_active.return_value = False
        av.audio_stream = stream
        assert asyncio.run(av.health_check()) is False

    def test_stop_releases_resources(self):
        av = AVCapture()
        cap, stream = MagicMock(), MagicMock()
        av.video_capture, av.audio_stream = cap, stream
        asyncio.run(av.stop())
        cap.release.assert_called_once()
        stream.close.assert_called_once()
        assert av.video_capture is None and av.audio_stream is None
