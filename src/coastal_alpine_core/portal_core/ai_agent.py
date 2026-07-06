import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from coastal_alpine_core import SovereignOllamaClient
from coastal_alpine_core.security import SecurityGuard, SecurityResult
from coastal_alpine_core.telemetry import DataFlywheel, TelemetryTracker, Trajectory

logger = logging.getLogger(__name__)
security_guard = SecurityGuard()

# Actuation values a plan may legally request. Anything else (e.g. an LLM
# hallucinating "super_high") reverts the whole plan to safe defaults.
ALLOWED_ACTION_VALUES = {
    "off", "on", "low", "medium", "high", "normal",
    "boost", "open", "closed", "reduce", "increase",
}


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
                # Collect and validate actuation requests. They stay at the
                # top level too — portal orchestrators read
                # plan.get("pump_action") etc. directly.
                actions = {}
                for k, v in plan_data.items():
                    if k.endswith("_action"):
                        value = str(v).lower()
                        if value not in ALLOWED_ACTION_VALUES:
                            logger.warning(
                                f"Plan requested unsupported actuation {k}={v!r}. "
                                "Reverting to safe defaults."
                            )
                            return self._generate_default_plan()
                        actions[k] = value

                validated = OptimizationPlan(
                    **{k: v for k, v in plan_data.items() if not k.endswith("_action")},
                    actions=actions,
                )
                plan = validated.model_dump()
                plan.update(actions)
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
        prompt = (
            "Analyze this environmental sensor snapshot and respond ONLY with a "
            "JSON object describing status and trends.\n"
            f"Readings: {json.dumps(sensor_data, default=str)}"
        )
        raw_text = ""
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(self.client.generate, prompt, model=self.model),
                timeout=30.0,
            )
            raw_text = response.get("response", "").strip()
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                analysis.setdefault("analysis_id", f"sens-{uuid.uuid4().hex[:12]}")
                analysis.setdefault("timestamp", datetime.now().isoformat())
                return analysis
            # Freeform reply — keep it as an observation rather than losing it
            return {
                "status": "unknown",
                "observations": raw_text,
                "analysis_id": f"sens-{uuid.uuid4().hex[:12]}",
                "timestamp": datetime.now().isoformat(),
            }
        except (asyncio.TimeoutError, TimeoutError):
            return {
                "status": "unknown",
                "observations": "LLM timeout during sensor analysis.",
                "analysis_id": f"sens-{uuid.uuid4().hex[:12]}",
                "timestamp": datetime.now().isoformat(),
            }
        except (json.JSONDecodeError, ValueError):
            return {
                "status": "unknown",
                "observations": raw_text,
                "analysis_id": f"sens-{uuid.uuid4().hex[:12]}",
                "timestamp": datetime.now().isoformat(),
            }

    async def process_visual_feedback(self, frame_data: bytes) -> dict:
        prompt = (
            "A camera frame from the growing area was captured. Respond ONLY "
            "with a JSON object assessing overall_health, anomalies, and confidence."
        )
        raw_text = ""
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(self.client.generate, prompt, model=self.model),
                timeout=30.0,
            )
            raw_text = response.get("response", "").strip()
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["frame_bytes"] = len(frame_data)
                return result
            return {
                "overall_health": "pending",
                "analysis": raw_text,
                "frame_bytes": len(frame_data),
            }
        except (asyncio.TimeoutError, TimeoutError, json.JSONDecodeError, ValueError):
            return {
                "overall_health": "pending",
                "analysis": raw_text or "LLM timeout during visual analysis.",
                "frame_bytes": len(frame_data),
            }

    async def process_audio_feedback(self, audio_data: bytes) -> dict:
        prompt = (
            "An audio sample from the equipment area was captured. Respond ONLY "
            "with a JSON object: anomaly_detected (bool), type, confidence."
        )
        raw_text = ""
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(self.client.generate, prompt, model=self.model),
                timeout=30.0,
            )
            raw_text = response.get("response", "").strip()
            json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                result["audio_bytes"] = len(audio_data)
                return result
            return {
                "anomaly_detected": False,
                "analysis": raw_text,
                "audio_bytes": len(audio_data),
            }
        except (asyncio.TimeoutError, TimeoutError, json.JSONDecodeError, ValueError):
            return {
                "anomaly_detected": False,
                "analysis": raw_text or "LLM timeout during audio analysis.",
                "audio_bytes": len(audio_data),
            }

    async def health_check(self) -> bool:
        """True only when Ollama responds AND the configured model is loaded."""
        try:
            listing = await asyncio.wait_for(
                asyncio.to_thread(self.client.list),
                timeout=5.0,
            )
            models = listing.get("models", []) if isinstance(listing, dict) else []
            return any(m.get("name", "").startswith(self.model) for m in models)
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    def record_hardware_result(self, plan_id: str, action: str, success: bool, **kwargs):
        self.flywheel.record_hardware_outcome(plan_id, action, success, **kwargs)

    def _generate_default_plan(self) -> dict:
        safe_actions = {"pump_action": "medium"}
        default_plan = OptimizationPlan(
            plan_id=f"opt-default-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            confidence_score=0.5,
            logistical_notes="Safe fallback parameters applied due to system exception or prompt blocking.",
            execution_window_minutes=30,
            requires_human_review=True,
            actions=safe_actions,
        )
        plan = default_plan.model_dump()
        # Mirror actions at the top level — portal orchestrators read
        # plan.get("pump_action") etc. directly.
        plan.update(safe_actions)
        return plan
