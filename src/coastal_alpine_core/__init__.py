"""
coastal-alpine-core: Shared utilities for Taranaki-based Coastal Alpine Tech Edge systems.
"""

from .ollama_client import SovereignOllamaClient
from .security import (
    SecurityGuard,
    SecurityResult,
    device_posture_check,
    input_guard_check,
    tenant_isolated_query,
)
from .telemetry import DataFlywheel, TelemetryTracker, Trajectory, log_performance

__version__ = "0.5.3"

__all__ = [
    "TelemetryTracker",
    "log_performance",
    "SovereignOllamaClient",
    "SecurityGuard",
    "SecurityResult",
    "input_guard_check",
    "device_posture_check",
    "tenant_isolated_query",
    "DataFlywheel",
    "Trajectory",
    "__version__",
]
