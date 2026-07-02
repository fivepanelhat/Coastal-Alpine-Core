import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from coastal_alpine_core import SovereignOllamaClient
from coastal_alpine_core.flywheel import DataFlywheel, Trajectory
from coastal_alpine_core.security import SecurityGuard, SecurityResult
from coastal_alpine_core.telemetry import TelemetryTracker

logger = logging.getLogger(__name__)
security_guard = SecurityGuard()


class OptimizationPlan(BaseModel):
    """Unified Optimization Plan for Coastal Alpine Portals."""

    plan_id: str
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    logistical_notes: str = Field(default="")
    execution_window_minutes: int = Field(default=15)
    requires_human_review: bool = Field(default=False)

    # Generic action fields
    actions: dict[str, str] = Field(default_factory=dict)


class AIAgent:
    def __init__(
        self,
        ollama_host: str = "http://localhost:11434",
        model: str = "gemma4:e4b",
        flywheel: DataFlywheel | None = None,
    ):
        self.ollama_host = ollama_host
        self.model = model
        self.client = SovereignOllamaClient(host=ollama_host, default_model=model)
        self.flywheel = flywheel or DataFlywheel(storage_path="flywheel_portal.jsonl")
        logger.info("Unified AI Agent initialized with full Data Flywheel support")

    @classmethod
    def from_config(cls, config: Any, flywheel: DataFlywheel | None = None):
        return cls(ollama_host=config.ollama.host, model=config.ollama.model, flywheel=flywheel)

    async def generate_optimization_plan(
        self, sensor_analysis: dict, visual_analysis: dict, audio_analysis: dict
    ) -> dict:
        inputs_str = (
            f"Sensors: {sensor_analysis}, Vision: {visual_analysis}, Audio: {audio_analysis}"
        )
        sec_result: SecurityResult = security_guard.check_prompt(inputs_str)
        if not sec_result.is_safe:
            logger.warning(f"Blocked by SecurityGuard: {sec_result.reason}")
            return self._generate_default_plan()

        measurement = TelemetryTracker.measure_latency("generate_optimization_plan")

        try:
            prompt = f"""Controller: Formulate a hardware actuation plan based on:
Sensors Analysis: {str(sensor_analysis)}
Visuals Ingestion: {str(visual_analysis)}
Acoustic Watchdog: {str(audio_analysis)}

Respond ONLY with a JSON object containing actions to take.
"""
            response = await asyncio.wait_for(
                asyncio.to_thread(self.client.generate, prompt, model=self.model),
                timeout=60.0,
            )

            text = response.get("response", "").strip()
            json_match = re.search(r"\{.*\}", text, re.DOTALL)

            if json_match:
                plan_data = json.loads(json_match.group())
                # Normalize actions if provided at top level
                actions = {}
                for k, v in list(plan_data.items()):
                    if k.endswith("_action"):
                        actions[k] = v.lower()
                        del plan_data[k]

                plan_data["actions"] = actions
                validated = OptimizationPlan(**plan_data)
                plan = validated.model_dump()
            else:
                logger.warning(
                    "AI optimization plan did not return structured JSON. Reverting to safe defaults."
                )
                return self._generate_default_plan()

            try:
                traj = Trajectory(
                    trajectory_id=str(uuid.uuid4()),
                    timestamp=datetime.now().isoformat(),
                    action="generate_optimization_plan",
                    input_summary=str(sensor_analysis)[:200],
                    output_summary=str(plan)[:300],
                    outcome="success",
                    latency_seconds=0.0,
                    estimated_energy_joules=0.0,
                    metadata={
                        "plan_id": plan.get("plan_id"),
                        "requires_human_review": plan.get("requires_human_review", False),
                    },
                )
                self.flywheel.record_trajectory(traj)
            except Exception as e:
                logger.warning(f"Flywheel recording failed: {e}")

            TelemetryTracker.complete_measurement(measurement, include_system_metrics=True)
            return plan

        except Exception as e:
            logger.error(f"Error generating optimization plan: {e}")
            return self._generate_default_plan()

    async def analyze_sensor_state(self, sensor_data: dict) -> dict:
        return {"status": "analyzed", "raw": sensor_data}

    async def process_visual_feedback(self, frame_data: bytes) -> dict:
        return {"status": "analyzed_vision"}

    async def process_audio_feedback(self, audio_data: bytes) -> dict:
        return {"status": "analyzed_audio"}

    async def health_check(self) -> bool:
        return True

    def record_hardware_result(self, plan_id: str, action: str, success: bool, **kwargs):
        self.flywheel.record_hardware_outcome(plan_id, action, success, **kwargs)

    def _generate_default_plan(self) -> dict:
        default_plan = OptimizationPlan(
            plan_id=f"opt-default-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            confidence_score=0.5,
            logistical_notes="Safe fallback parameters applied due to system exception or prompt blocking.",
            execution_window_minutes=30,
            requires_human_review=True,
            actions={},
        )
        return default_plan.model_dump()
