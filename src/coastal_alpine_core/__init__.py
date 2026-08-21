"""
coastal-alpine-core: Shared utilities for Taranaki-based Coastal Alpine Tech Edge systems.
"""

from .ollama_client import SovereignOllamaClient
from .security import (
    SecurityGuard,
    SecurityResult,
    clear_firmware_baselines,
    device_posture_check,
    input_guard_check,
    register_firmware_baseline,
    tenant_isolated_query,
)
from .session_events import (
    EVENT_TYPES,
    SessionEvent,
    SessionEventStore,
    make_event,
)
from .telemetry import DataFlywheel, TelemetryTracker, Trajectory, log_performance

__version__ = "0.5.7"

__all__ = [
    "TelemetryTracker",
    "log_performance",
    "SovereignOllamaClient",
    "SecurityGuard",
    "SecurityResult",
    "input_guard_check",
    "device_posture_check",
    "register_firmware_baseline",
    "clear_firmware_baselines",
    "tenant_isolated_query",
    "DataFlywheel",
    "Trajectory",
    "SessionEvent",
    "SessionEventStore",
    "make_event",
    "EVENT_TYPES",
    "__version__",
]
